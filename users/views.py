from rest_framework.generics import RetrieveUpdateAPIView

from users.serializers import UserSerializer


class MeView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user
