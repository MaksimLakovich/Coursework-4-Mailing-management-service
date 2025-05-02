from django.urls import path
from users.views import UserStartView, UserRegisterView

app_name = "users"

urlpatterns = [
    path("start/", UserStartView.as_view(), name="start_page"),
    path("register/", UserRegisterView.as_view(), name="register_page"),
    # path("login/", CustomLoginView.as_view(), name="login"),
    # path("logout/", LogoutView.as_view(), name="logout"),
    # path("edit_profile/", CustomEditProfileView.as_view(), name="edit_profile"),
    # path("change_password/", CustomPasswordChangeView.as_view(), name="change_password"),
]
