from flask_security.forms import (
    RegisterForm,
    LoginForm,
    StringField,
    PasswordField,
    ValidationError,
    Required,
    Length,
    EqualTo,
    unique_user_email,
    email_required,
    email_validator,
    password_required,
    _datastore,
)

name_required = Required(message="没有输入名字")
name_length = Length(min=3, max=20, message="长度要在3 - 20之间")


def unique_user_name(form, field):
    if _datastore.get_user_name(field.data) is not None:
        raise ValidationError(f"{field.data} 已经被占用了")
    if "@" in field.data:
        raise ValidationError("名字中不能使用@")


class ExtendedRegisterForm(RegisterForm):
    name = StringField("名字", validators=[name_required, name_length, unique_user_name])
    email = StringField(
        "邮箱", validators=[email_required, email_validator, unique_user_email]
    )
    password = PasswordField("密码", validators=[password_required])
    password_confirm = PasswordField(
        "确认密码",
        validators=[
            EqualTo("password", message="RETYPE_PASSWORD_MISMATCH"),
            password_required,
        ],
    )


class ExtendedLoginForm(LoginForm):
    email = StringField("邮箱/用户名", validators=[Required(message="未输入账号内容")])
    password = PasswordField("密码", validators=[password_required])

