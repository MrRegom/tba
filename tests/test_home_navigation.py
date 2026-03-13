import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse


@pytest.mark.django_db
def test_regular_user_lands_on_informative_home(client):
    user = User.objects.create_user(username='solicitante-home', password='secret')
    user.groups.add(Group.objects.create(name='Solicitante'))
    client.force_login(user)

    response = client.get(reverse('dashboard'))

    assert response.status_code == 200
    assert 'Inicio del sistema' in response.content.decode()
    assert 'Solicitudes Pendientes' not in response.content.decode()
    assert reverse('dashboard_operativo') not in response.content.decode()


@pytest.mark.django_db
def test_regular_user_is_redirected_away_from_operational_dashboard(client):
    user = User.objects.create_user(username='solicitante-dashboard', password='secret')
    user.groups.add(Group.objects.create(name='Solicitante'))
    client.force_login(user)

    response = client.get(reverse('dashboard_analytics'))

    assert response.status_code == 302
    assert response.url == reverse('dashboard')


@pytest.mark.django_db
def test_manager_role_can_open_operational_dashboard(client):
    user = User.objects.create_user(username='encargado-bodega', password='secret')
    user.groups.add(Group.objects.create(name='Encargado de Bodega'))
    client.force_login(user)

    response = client.get(reverse('dashboard_analytics'))

    assert response.status_code == 200
    assert 'Solicitudes Pendientes' in response.content.decode()


@pytest.mark.django_db
def test_manager_home_shows_dashboard_shortcut(client):
    user = User.objects.create_user(username='admin-inst', password='secret')
    user.groups.add(Group.objects.create(name='Administrador Institucional'))
    client.force_login(user)

    response = client.get(reverse('dashboard'))

    assert response.status_code == 200
    assert reverse('dashboard_operativo') in response.content.decode()
