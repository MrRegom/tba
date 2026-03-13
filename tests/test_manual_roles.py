import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse


@pytest.mark.django_db
def test_manual_uses_user_roles_for_profiles(client):
    user = User.objects.create_user(username='sol-user', password='secret')
    role = Group.objects.create(name='Solicitante')
    user.groups.add(role)
    client.force_login(user)

    response = client.get(reverse('pages:manual'))

    assert response.status_code == 200
    assert response.context['manual_profile_keys'] == ['solicitante']
    assert response.context['manual_default_profile'] == 'solicitante'


@pytest.mark.django_db
def test_manual_without_official_roles_falls_back_to_general_content(client):
    user = User.objects.create_user(username='no-role-user', password='secret')
    client.force_login(user)

    response = client.get(reverse('pages:manual'))

    assert response.status_code == 200
    assert response.context['manual_profile_keys'] == []
    assert response.context['manual_default_profile'] == 'todos'
