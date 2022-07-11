from kanpai import Kanpai

changePasswordSchema = Kanpai.Object({
    "currentPassword": Kanpai.String().required("Please enter your current password"),
    "newPassword": Kanpai.String().required("Please enter your new password"),
    "cPassword": Kanpai.String().required("Please re-enter your new password")
})

resetPasswordSchema = Kanpai.Object({
    "email": Kanpai.String().required("Please enter your current password")
})

updateEmailSchema = Kanpai.Object({
    "email": Kanpai.String().trim().match(r'[^@]+@[^@]+\.[^@]+', error="Please enter valid email").required("Please enter your email"),
    "currentPassword": Kanpai.String().required("Please enter your current password"),
    "code": Kanpai.String().required("Please enter the code you received")
})

updateSchema = Kanpai.Object({
    "name": Kanpai.String(),
    "avatar": Kanpai.String(),
    "achievement": Kanpai.String(),
    "googleSignIn": Kanpai.String(),
    "exp": Kanpai.String(),
    "level": Kanpai.String(),
    "gender": Kanpai.String(),
    "biodata": Kanpai.String(),
    "phoneNumber": Kanpai.String(),
    "status": Kanpai.String()
})

registerAccountSchema = Kanpai.Object({
    "name": Kanpai.String().required("Please enter your name"),
    "email": Kanpai.String().trim().match(r'[^@]+@[^@]+\.[^@]+', error="Please enter valid email").required("Please enter your email"),
    "password": Kanpai.String().required("Please enter your password"),
    "cPassword": Kanpai.String().required("Please enter your confirmation password")
})

