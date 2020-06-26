from django.test import TestCase

# Create your tests here.
from rest_framework.test import APIRequestFactory
from rest_framework.test import RequestsClient

factory = APIRequestFactory()
request = factory.post('', format='json')
print(request)
# response = client.get('http://127.0.0.1:8000/quiz/')
# print(response)

# csrftoken = response.cookies['csrftoken']
#
# response = client.post('http://127.0.0.1:8000/quiz/login_submit/', json={
#     'username': 'admin',
#     'password': 'admin123'
# }, headers={'X-CSRFToken': csrftoken})
# assert response.status_code == 200
