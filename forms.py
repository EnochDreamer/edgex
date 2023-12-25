from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, SelectField, SelectMultipleField, DateTimeField, BooleanField,PasswordField,StringField,FileField,TextAreaField,IntegerField
from wtforms import validators
from flask_pagedown.fields import PageDownField

class LoginForm(FlaskForm):
    email = EmailField(
        'email',
       [ validators.InputRequired(message='please input email'),
       validators.Length(max=30,message='too many email characters')
       ]
    )
    password = PasswordField(
        'password',
        [validators.InputRequired(message='please input password'),
        validators.Length(min=5, max=15,message='too many password characters')]
    )
    remember = BooleanField(
        'remember'
    )

class SignUpForm(FlaskForm):
    name = StringField(
        'name',
       [ validators.InputRequired(message='please input Fullname'),
       validators.Length(max=150,message='too many  characters')
       ])
    email = EmailField(
        'email',
       [ validators.InputRequired(message='please input email'),
       validators.Length(max=30,message='too many email characters')
       ])
    address = StringField(
        'address',
       [ validators.InputRequired(message='please input address'),
       validators.Length(max=250,message='too many  characters')
       ])
    password = PasswordField(
        'password',
        [validators.InputRequired(message='please input password'),
        validators.EqualTo('verify_password',message="passwords don't match"),
        validators.Length(min=5, max=15,message='too many password characters')]
    )
    verify_password = PasswordField(
        'verify_password',
        [validators.InputRequired(message='please verify password'),
        validators.Length(min=5, max=15,message='too many password characters')]
    )

class AddCourseForm(FlaskForm):
    name = StringField(
    'name',
    [ validators.InputRequired(message='please input course name'),
    validators.Length(max=30,message='too many characters')
    ])
    description = TextAreaField(
    'description',
    [ validators.InputRequired(message='please input description'),
    validators.Length(max=100,message='too many characters')
    ])
    price = IntegerField(
    'price',
    [ validators.InputRequired(message='please input price'),
         validators.NumberRange(min=0,message='enter a number greater than 0')
    ])

    duration=IntegerField(
        'duration',
        [validators.InputRequired(message='please enter duration'),
         validators.NumberRange(min=0,message='enter a number greater than 0')])

    image=FileField(
        'image',
        
        []
    )
class AddTopicForm(FlaskForm):
    title=StringField(
        'title',
        [ validators.InputRequired(message='please input topic title'),
    validators.Length(max=30,message='too many characters')
    ])
    topic_no=IntegerField(
        'topic_no',
        [validators.InputRequired(message='please select topic no.'),
        validators.NumberRange(min=0,max=12,message='pick a unique number between 1 and 12')
        ]
    )
    free = BooleanField(
        'free'
    )
    # content=TextAreaField(
    #     'content',
    #     [validators.InputRequired(message='please enter topic content')]
    # )
    content=PageDownField(
        'pagedown',
        [validators.InputRequired(message='please enter topic content')]
        
    )

class AddSubscriptionForm(FlaskForm):
    user_id=IntegerField(
        'user_id',
        [validators.InputRequired(message='please enter user id'),
         validators.NumberRange(min=0,message='enter a number greater than 0')]
    )
    course_id=IntegerField(
        'course_id',
        [validators.InputRequired(message='please enter courese id'),
         validators.NumberRange(min=0,message='enter a number greater than 0')]
    )
    duration=IntegerField(
        'duration',
        [validators.InputRequired(message='please enter duration'),
         validators.NumberRange(min=0,message='enter a number greater than 0')
        ])

class SearchForm(FlaskForm):
    search=StringField(
        'search',
        [validators.InputRequired(message='please select topic no.')]

    )

# class VenueForm(Form):
#     name = StringField(
#         'name', validators=[DataRequired()]
#     )
#     city = StringField(
#         'city', validators=[DataRequired()]
#     )