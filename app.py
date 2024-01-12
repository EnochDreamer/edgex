from flask import Flask,render_template,request,redirect,url_for,abort,flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db_setup,Anonymous,User,Course,Topic,Comment,Reply,Subscription
from flask_migrate import Migrate
from datetime import datetime,timedelta
from forms import LoginForm,SignUpForm,AddCourseForm,AddTopicForm,AddSubscriptionForm
from flask_login import LoginManager,login_required,login_user,logout_user,current_user
from flask_pagedown import PageDown
from auth import requires_auth
from markdown import markdown
import dateutil.parser
import babel
import requests
import boto3

ssm = boto3.client('ssm', 'us-east-1')
def get_parameters():
    response = ssm.get_parameters(
        Names=['paystack'],WithDecryption=True
    )
    for parameter in response['Parameters']:
        print(parameter)
        return parameter['Value']


app=Flask(__name__)

PageDown(app)
db_setup(app,Migrate)
# @app.route('/signup',methods=['GET','POST'])
# def signup():
#     form=SignUpForm()
#     if request.methods=='GET':
#         return render_template('signup.html',form=form)
#     if form.validate_on_submit():

def paginate_items(items,request=request,per_page=5):
        page = request.args.get('page', 1, type=int)
        start = (page-1)*per_page
        end = start + per_page
        items_list = [item for item in items]
        result = items_list[start:end]
        return items_list

def redirect_dest(fallback,request=request):
        dest = request.form.get('next_page')
        if dest:
            return redirect(dest)
        else:
            return redirect(url_for(fallback))
         

#@app.template_filter('datetime')
def format_datetime(value, format='medium'):
    new_value=str(value)
    date = dateutil.parser.parse(new_value)
    if format == 'long':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'short':
        format="EE MM, dd, y h:mma"
    elif format=='narrow':
        format=""
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime
app.jinja_env.filters['markdown'] = markdown

def expire_subscriptions(user):
    print("hello from expire")
    for subscription in user.subscriptions:
        if datetime.now()>subscription.expiry_date:
            subscription.delete()

###########LOGIN LOGIC##########
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'
login_manager.anonymous_user=Anonymous
@login_manager.user_loader
def load_user(user_id):
    print("user loader")
    return User.query.filter_by(alternative_id=user_id).first()

@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).one_or_none()
        if user is None:
            abort(404)
        if not user.verify_password(form.password.data):  
            abort(401)
        login_user(user,remember=form.remember.data)
        print("logged in")
        print(current_user.format())
        flash("Login Successful!")
        expire_subscriptions(current_user)
        next_page=request.form.get('next_page')
        # next page is either 'http://localhost/None' or 'htttp://localhost/some_endpoint
        if ('None' not in next_page):
            print('next triggered')
            return redirect(next_page)
        else:
            print('home')
            return redirect(url_for('home'))
    if form.errors:
        return redirect(url_for('login'))
    if request.method=='GET':
        return render_template('login.html',form=form)
    

@app.route('/signup',methods=['GET','POST'])
def signup():
    form=SignUpForm()
    if form.validate_on_submit():
        user_exists=User.query.filter_by(email=form.email.data).first()
        if user_exists:
            abort(422)
        new_user=User(email=form.email.data,name=form.name.data,address=form.address.data)
        new_user.hash_password(form.password.data)
        new_user.insert()
        flash("Sign-up Successful")
        return redirect(url_for('login'))
    if form.errors:
        flash(form.errors)
        return redirect(url_for('login'))
    if request.method=='GET':
        return render_template('signup.html',form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
    
################################

    
    

#user=User.query.filter_by(id=1).one()
    #course=Course.query.filter(Course.id==3).one()
    #users=User.query.join(Subscription).filter(Subscription.course_id==course.id).all()
    #print([item.email for item in users])
    #print(course in user.subscribed())    

@app.route('/')
def home():
    print(current_user.format())
    search_term=request.args.get('search')
    if search_term:
        results=Course.query.filter(Course.name.ilike(f'%{search_term}%')).all()
        return render_template('search_result.html',courses=results,user=current_user,search_term=search_term)
    courses=Course.query.filter_by(published=True).all()
    return render_template('home.html',courses=courses,user=current_user)

@app.route('/courses', methods=['GET','POST'])
@requires_auth(current_user)
@login_required
def new_course():
    form=AddCourseForm()
    if form.validate_on_submit():
        new_course=Course(name=form.name.data,creator_id=current_user.id,description=form.description.data,price=form.price.data,duration=form.duration.data)
        new_course.save_image(form.image.data)
        new_course.commit()
        flash('Item added successfuly!')
        return redirect(url_for('room'))
    if form.errors:
        flash(form.errors)
        return redirect(url_for('login'))
    if request.method=='GET':
        return render_template('addCourse.html',form=form)
    
    
@app.route('/courses/<int:course_id>', methods=['GET'])
def course_content(course_id):
    expire_subscriptions(current_user)
    course=Course.query.filter_by(id=course_id).one_or_none()
    if course is None:
        abort(404)
    topics=Topic.query.filter_by(course_id=course_id).order_by(Topic.topic_no).all()
    return render_template('topics.html',course=course,course_id=course_id,topics=[topic for topic in topics],user=current_user)

@app.route('/courses/<int:course_id>/topics', methods=['GET', 'POST'])
@requires_auth(current_user)
@login_required
def new_topic(course_id):
    form=AddTopicForm()
    if request.method=='POST':
        topic_no_exists=Topic.query.filter_by(course_id=course_id,topic_no=form.topic_no.data).one_or_none()
        if topic_no_exists:
            flash("Topic number already used")
            return redirect(url_for('new_topic',course_id=course_id))
        elif form.validate_on_submit():
            new_topic=Topic(title=form.title.data,topic_no=form.topic_no.data,content=form.content.data,course_id=course_id,free=form.free.data)
            try:
                new_topic.commit()
            except Exception:
                new_topic.rollback()
                abort(400)
                
            flash('Item added successfuly!')
            return redirect(url_for('course_content',course_id=course_id))
    if request.method=='GET':
        topic_count=Topic.query.filter_by(course_id=course_id).count()
        return render_template('addTopic.html',form=form,course_id=course_id,next_no=(topic_count+1))
@app.route('/payment/<int:course_id>',methods=['GET','POST'])
@login_required
def pay(course_id):
        course=Course.query.filter_by(id=course_id).one_or_none()
        if course in current_user.subscribed():
            flash("you are already  subscribed for this course")
            return redirect(url_for('course_content',course_id=course_id))
        if course is None:
            abort(404)
        return render_template('pay.html',course=course,user=current_user)
    

@app.route('/courses/<int:course_id>/<int:topic_no>')
@login_required
def content(topic_no,course_id):
    expire_subscriptions(current_user)
    topic=Topic.query.filter_by(topic_no=topic_no,course_id=course_id).one_or_none()
    if topic is None:
        abort(404)
    if (current_user.admin or current_user.superuser or (current_user in (topic.course.subscribers())) or topic.free):
        topic_count=Topic.query.filter_by(course_id=course_id).count()
        return render_template('content.html',topic=topic,topic_count=topic_count,user=current_user,course_id=course_id)
    elif not(current_user in (topic.course.subscribers())):
        return redirect(url_for('pay',course_id=course_id))
    else:
        abort(403)

@app.route('/room')
@requires_auth(current_user)
@login_required
def room():
    if current_user.admin:
        my_courses=Course.query.filter_by(creator_id=current_user.id).order_by(Course.created_at).all()
    if current_user.superuser:
        my_courses=Course.query.filter_by(published=False).order_by(Course.created_at).all()
    return render_template('room.html',my_courses=my_courses,user=current_user)

@app.route('/publish/<int:course_id>')
@login_required
def publish(course_id):
    if current_user.superuser:
        course=Course.query.filter_by(id=course_id).one_or_none()
        if course is None:
            abort(404)
        course.published=True
        try:
            course.commit()
            flash("course published!")
            return redirect(url_for('room'))
        except Exception:
            flash("couldn't publish course!")
            return redirect(url_for('room'))

    
@app.route('/edit_course/<int:course_id>',methods=['GET','POST'])
@requires_auth(current_user)
@login_required
def edit_course(course_id):
    form=AddCourseForm()
    course=Course.query.filter_by(id=course_id).one_or_none()
    if course is None:
            abort(404)
    if request.method=='GET':
        form.name.default=course.name
        form.description.default=course.description
        form.price.default=course.price
        form.duration.default=course.duration
        form.image.default=course.image
        form.process()
        return render_template('edit_course.html',form=form,course_id=course_id)
    if request.method=='POST':
        if form.validate_on_submit():
            course.name=form.name.data
            course.description=form.description.data
            course.price=form.price.data
            course.duration=form.duration.data
            course.published=False
            if form.image.data:
                course.save_image(form.image.data)
            try:
                course.commit()
                flash("Course updated !")
                return redirect(url_for('home'))
            except Exception:
                course.rollback()
                flash("Could not update Course")
                return redirect(url_for('room'))
        else:
            print(form.errors)
@app.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course=Course.query.filter_by(id=course_id).one_or_none()
    try:
        course.delete()
        flash("Item deleted successfully!")
        return redirect(url_for('home'))
    except Exception:
        course.rollback()
        flash("could not deete Item")
        return redirect(url_for('home'))
    
@app.route('/edit_topic/<int:topic_id>',methods=['GET','POST'])
@requires_auth(current_user)
@login_required
def edit_topic(topic_id):
    form=AddTopicForm()
    topic=Topic.query.filter_by(id=topic_id).one_or_none()
    if not ((current_user.superuser) or (topic.short()['creator_id']==current_user.id) ):
        abort(403)
    if topic is None:
            abort(404)
    if request.method=='GET':
        form.title.default=topic.title
        form.content.default=topic.content
        form.topic_no.default=(topic.topic_no)
        form.free.default=topic.free
        form.process()
        return render_template('edit_topic.html',form=form,course_id=topic.course_id,topic=topic)
    if request.method=='POST':
        if form.validate_on_submit():
            topic.title=form.title.data
            topic.content=form.content.data
            topic.free=form.free.data
            topic.topic_no=form.topic_no.data
            try:
                topic.commit()
                flash("topic updated !")
                course=Course.query.filter_by(id=topic.course_id).one()
                course.published=False
                course.commit()
                return redirect(url_for('course_content',course_id=topic.course_id))
            except Exception:
                topic.rollback()
                flash("Could not update Course")
                return redirect(url_for('edit_course',topic_id=topic.id))
        else:
            print(form.errors)

@app.route('/topics/<int:topic_id>/delete', methods=['POST'])
@requires_auth(current_user)
@login_required
def delete_topic(topic_id):
    topic=Topic.query.filter_by(id=topic_id).one_or_none()
    if topic is None:
        abort(404)
    try:
        topic.delete()
        flash("Item deleted successfully!")
        return redirect(url_for('course_content',course_id=topic.course_id))
    except Exception:
        topic.rollback()
        flash("could not deete Item")
        return redirect(url_for('course_content',course_id=topic.course_id))

@app.route('/subscriptions')
@login_required
def subscriptions():
    return render_template('subscriptions.html',user=current_user)

@app.route('/add_subscription', methods=['GET', 'POST'])
@requires_auth(current_user)
@login_required
def add_subscription():
    form=AddSubscriptionForm()
    if request.method=='GET':
        return render_template('add_subscription.html',form=form)
    if request.method=='POST':
        if form.validate_on_submit():
            print(form.duration.data)
            subscription=Subscription.query.filter_by(user_id=form.user_id.data,course_id=form.course_id.data).one_or_none()
            if subscription:
                flash("Subscription already exists")
                return redirect(url_for('add_subscription'))
            new_subscription=Subscription(user_id=form.user_id.data,course_id=form.course_id.data,expiry_date=(datetime.now() + timedelta(days=form.duration.data)))
            try:
                new_subscription.commit()
                flash("Subscription created successfully")
                return redirect(url_for('room'))
            except Exception:
                new_subscription.rollback()
                flash("Could not create subscription, check and try again")
                return redirect(url_for('add_subscription'))
        else:
            print(form.errors)
@app.route('/users')
@requires_auth(current_user)
@login_required
def users():
    search_term=request.args.get("search")
    if search_term:
        result=User.query.filter(User.email.ilike(f"%{search_term}%"),User.id!=current_user.id).all()
        return render_template("user_search_result.html", app_users=result,user=current_user,search_term=search_term)
    users=User.query.filter(User.id!=current_user.id).order_by(User.email).all()
    return render_template('users.html',app_users=users,user=current_user)

@app.route('/<int:user_id>/switch_admin', methods=['POST'])
@requires_auth(current_user)
@login_required
def switch_admin(user_id):
    if not current_user.superuser:
        abort(403)
    user=User.query.filter_by(id=user_id).one_or_none()
    if user is None:
        abort(404)
    user.admin=False if (user.admin) else True
    user.insert()
    user=User.query.filter_by(id=user_id).one_or_none()
    if user.admin:
        flash(f"user {user.email} is now an admin!")
    else:
        flash(f"user {user.email} is no longer an admin!")
    return redirect(url_for('users'))

@app.route('/courses/<int:course_id>/verify_pay/<reference>/')
@login_required
def verify_pay(course_id,reference):
    url=f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        'Authorization': get_parameters(),
    }
    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )
    print(response.json())
    res=response.json()['data']
    print(res)
    if not (res['status']=='success'):
        abort(422)
    print(request.args.get('amount'))
    if not (int(res['amount'])==int(request.args.get('amount'))):
        abort(422)
    duration =Course.query.filter_by(id=course_id).one().duration
    new_subscription=Subscription(user_id=current_user.id,course_id=course_id,expiry_date=(datetime.now() + timedelta(days=int(duration))))
    try:
        new_subscription.commit()
        flash("Subscription created successfully")
        return jsonify({
            "success":True
        })
    except Exception:
        new_subscription.rollback()
        flash("Could not create subscription, check and try again")
        return redirect(url_for('pay',course_id=course_id))

    
    



if __name__=='__main__':
    app.run(debug=True)
    
