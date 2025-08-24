import sys
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,LoginManager,AnonymousUserMixin
from uuid import uuid4
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()



# def get_parameters():
#     response = ssm.get_parameters(
#         Names=['database'],WithDecryption=True
#     )
#     for parameter in response['Parameters']:
#         return parameter['Value']
db_host=os.environ.get('RDS_HOSTNAME')
db_port=os.environ.get('RDS_PORT')
db_name=os.environ.get('RDS_DB_NAME')
db_username=os.environ.get('RDS_USERNAME')
db_password=os.environ.get('RDS_PASSWORD')

db = SQLAlchemy()
database_path = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'
def db_setup(app, Migrate, database_path=database_path, db=db):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"]=os.environ.get('APP_SECRET_KEY')
    db.app = app
    db.init_app(app)
    migrate=Migrate(app,db)
    return db


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.email='welcome@buddy!'
        self.name='XAnon'
        self.address='Moon'
        self.paid=False
        self.admin=False
        self.superuser=False
        self.subscriptions=[]
        self.alternative_id=''
    def subscribed(self):
        return []
    def format(self):
        return ({
                'id':0,
                'email':self.email,
                "admin":self.admin,
                "paid":self.paid,
                "superuser":self.superuser,
                'is_authenticated':False,
                "paid":False
            })


class Subscription(db.Model):
    """Generates a many-to-many relationship when a user subscribes to a course"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    expiry_date=db.Column(db.DateTime)

    def commit(self):
        db.session.add(self)
        db.session.commit()
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def rollback(self):
        db.session.rollback()

class User(UserMixin,db.Model):
    __tablename__='my_user'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(150))
    email=db.Column(db.String(100),nullable=False,unique=True)
    address=db.Column(db.String(250))
    superuser=db.Column(db.Boolean,default=False)
    admin=db.Column(db.Boolean,nullable=False,default=False)
    password_hash=db.Column(db.String())
    alternative_id=db.Column(db.String())
    courses=db.relationship('Course', backref='creator',lazy=True)
    subscriptions=db.relationship('Subscription', backref='user',lazy=True)
    replies=db.relationship('Reply', backref='replyer',lazy=True)
    comments=db.relationship('Comment', backref='commenter',lazy=True)
    def get_id(self):
        return str(self.alternative_id)
    def subscribed(self):
        return [subscription.course for subscription in self.subscriptions]
    def hash_password(self,password):
        self.password_hash=generate_password_hash(password)
        self.alternative_id=generate_password_hash(str(self.id)+password)
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)
    def insert(self):
        db.session.add(self)
        db.session.commit()
    
    def format(self):
        return(
            {
                "id":self.id,
                "email":self.email,
                "admin":self.admin,
                "is_authenticated":True,
                "superuser":self.superuser
            })





class Course(db.Model):
    __tablename__='course'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(), nullable=False)
    published=db.Column(db.Boolean,default=False)
    price=db.Column(db.String,default="$100")
    duration=db.Column(db.String)
    image=db.Column(db.String(),default='IMG-20220512-WA0011.jpg')
    description=db.Column(db.String())
    creator_id=db.Column(db.Integer, db.ForeignKey('my_user.id'))
    created_at=db.Column(db.String() ,default=(datetime.now()).strftime("%d/%m/%Y"))
    topics=db.relationship('Topic', backref='course',lazy=True)
    subscriptions=db.relationship('Subscription', backref='course',lazy=True)
    def subscribers(self):
        return [subscription.user for subscription in self.subscriptions]
    def commit(self):
        db.session.add(self)
        db.session.commit()
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def rollback(self):
        db.session.rollback()
    def format(self):
        return {
            "id":self.id,
            "course":self.course,
            "description":self.description,
            "created_at":self.created_at,
            "creator":self.creator.format(),
            "published":self.published,
            "subscribers":[subscription.user.email for subscription in self.subscriptions]
        }
    def save_image(self, file):
        """Saves an image from `request.files`"""
        _, fmt = os.path.splitext(file.filename)
        newFileName = str(uuid4()).replace('-', '') + fmt
        os.makedirs(os.path.join('static', 'img', 'course_image'), exist_ok=True)
        path = os.path.join("static", "img", "course_image", newFileName)
        print(path)
        file.save(path)
        self.image = newFileName
        db.session.commit()

class Topic(db.Model):
    __tablename__='topic'
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(), nullable=False)
    free=db.Column(db.Boolean,default=False)
    content=db.Column(db.String(), nullable=False)
    topic_no=db.Column(db.Integer,nullable=True)
    course_id=db.Column(db.Integer, db.ForeignKey('course.id'))
    created_at=db.Column(db.String() ,default=(datetime.now()).strftime("%d/%m/%Y"))
    comments=db.relationship('Comment', backref='post',lazy=True)
    def commit(self):
        db.session.add(self)
        db.session.commit()
    def rollback(self):
        db.session.rollback()
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def short(self):
        return{
            "id":self.id,
            "title":self.title,
            "created_at":self.created_at,
            "topic_no":self.topic_no,
            "free":self.free,
            "course_id":self.course_id,
            "creator_id":self.course.creator_id
        }
    def format(self):
        return {
            "id":self.id,
            "title":self.title,
            "content":self.content,
            "created_at":(self.created_at).strftime("%d/%m/%Y")
        }



class Comment(db.Model):
   
    comment=db.Column(db.String(),nullable=False)
    id=db.Column(db.Integer, primary_key=True)
    topic_id=db.Column(db.Integer, db.ForeignKey('topic.id'))
    commenter_id=db.Column(db.Integer, db.ForeignKey('my_user.id'))
    
    def format(self):
        return {
            "id":self.id,
            "comment":self.comment,
            "commenter":self.commenter.format()
        }

class Reply(db.Model):
   
    reply=db.Column(db.String(),nullable=False)
    id=db.Column(db.Integer, primary_key=True)
    comment_id=db.Column(db.Integer, db.ForeignKey('comment.id'))
    user_id=db.Column(db.Integer,db.ForeignKey('my_user.id'))
    
    def format(self):
        return {
            "id":self.id,
            "comment":self.comment,
            "user":self.replyer.format()
        }

