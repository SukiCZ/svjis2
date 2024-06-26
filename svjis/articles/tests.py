from django.test import TestCase
from django.urls import reverse
from .models import Article, ArticleMenu
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group, Permission


groups = {
    'owner': [
        'svjis_add_article_comment',
        'svjis_view_personal_menu',
        'svjis_view_phonelist',
        'svjis_answer_survey',
    ],
    'board_member': [
        'svjis_add_article_comment',
        'svjis_view_personal_menu',
        'svjis_view_phonelist',
    ],
    'vendor': [
        'svjis_add_article_comment',
        'svjis_view_personal_menu',
    ],
    'redactor': [
        'svjis_view_redaction_menu',
        'svjis_edit_article',
        'svjis_edit_article_menu',
        'svjis_edit_survey',
        'svjis_edit_article_news',
    ],
    'admin': [
        'svjis_view_redaction_menu',
        'svjis_edit_article',
        'svjis_add_article_comment',
        'svjis_edit_article_menu',
        'svjis_edit_article_news',
        'svjis_view_admin_menu',
        'svjis_edit_admin_users',
        'svjis_edit_admin_groups',
        'svjis_view_personal_menu',
        'svjis_edit_admin_preferences',
        'svjis_edit_admin_company',
        'svjis_edit_admin_building',
        'svjis_view_phonelist',
    ],
}

users = {
    'jiri': {
        'first_name': 'Jiří',
        'last_name': 'Brambůrek',
        'password': 'jiri',
        'email': 'jiri@test.cz',
    },
    'petr': {
        'first_name': 'Petr',
        'last_name': 'Nebus',
        'password': 'petr',
        'email': 'petr@test.cz',
    },
    'karel': {
        'first_name': 'Karel',
        'last_name': 'Lukáš',
        'password': 'karel',
        'email': 'karel@test.cz',
    },
    'jarda': {
        'first_name': 'Jaroslav',
        'last_name': 'Beran',
        'password': 'jarda',
        'email': 'jarda@test.cz',
    },
}


def create_group(name):
    gobj = Group(name=name)
    gobj.save()
    for p in groups[name]:
        pobj = Permission.objects.get(content_type__app_label='articles', codename=p)
        gobj.permissions.add(pobj)
    return gobj


def create_user(name, groups):
    u = User.objects.create(
        username=name,
        email=users[name]['email'],
        password=make_password(users[name]['password']),
        first_name=users[name]['first_name'],
        last_name=users[name]['last_name'],
    )
    u.is_active = True
    u.save()
    for g in groups:
        u.groups.add(g)
    return u


class ArticleListTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.g_owner = create_group('owner')
        cls.g_board_member = create_group('board_member')
        cls.g_vendor = create_group('vendor')
        cls.g_redactor = create_group('redactor')
        cls.g_admin = create_group('admin')

        cls.u_jiri = create_user('jiri', [cls.g_owner, cls.g_board_member, cls.g_redactor])
        cls.u_petr = create_user('petr', [cls.g_owner])
        cls.u_karel = create_user('karel', [cls.g_vendor])
        cls.u_jarda = create_user('jarda', [cls.g_owner, cls.g_board_member, cls.g_admin])

        cls.menu_docs = ArticleMenu.objects.create(description='Documents')

        cls.article_not_published = Article.objects.create(
            header='Not Published',
            perex='test perex',
            body='test body',
            menu=cls.menu_docs,
            author=cls.u_jiri,
            published=False,
            visible_for_all=True,
        )
        cls.article_for_no_one = Article.objects.create(
            header='For no one',
            perex='test perex',
            body='test body',
            menu=cls.menu_docs,
            author=cls.u_jiri,
            published=True,
            visible_for_all=False,
        )
        cls.article_for_all = Article.objects.create(
            header='For All',
            perex='test perex',
            body='test body',
            menu=cls.menu_docs,
            author=cls.u_jiri,
            published=True,
            visible_for_all=True,
        )
        cls.article_for_owners = Article.objects.create(
            header='For Owners',
            perex='test perex',
            body='test body',
            menu=cls.menu_docs,
            author=cls.u_jiri,
            published=True,
            visible_for_all=False,
        )
        cls.article_for_owners.visible_for_group.add(cls.g_owner)
        cls.article_for_owners_and_board = Article.objects.create(
            header='For Owners and Board',
            perex='test perex',
            body='test body',
            menu=cls.menu_docs,
            author=cls.u_jiri,
            published=True,
            visible_for_all=False,
        )
        cls.article_for_owners_and_board.visible_for_group.add(cls.g_owner)
        cls.article_for_owners_and_board.visible_for_group.add(cls.g_board_member)
        cls.article_for_board = Article.objects.create(
            header='For Board',
            perex='test perex',
            body='test body',
            menu=cls.menu_docs,
            author=cls.u_jiri,
            published=True,
            visible_for_all=False,
        )
        cls.article_for_board.visible_for_group.add(cls.g_board_member)

    def test_admin_user(self):
        # Login user
        logged_in = self.client.login(username='jarda', password=users['jarda']['password'])
        self.assertEqual(logged_in, True)

        # Article for all
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_all.slug}))
        self.assertEqual(response.status_code, 200)

        # Article for Board
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 200)

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Menu
        res_tray_menu = response.context['tray_menu_items']
        self.assertEqual(len(res_tray_menu), 5)
        self.assertEqual(res_tray_menu[0]['description'], 'Articles')
        self.assertEqual(res_tray_menu[1]['description'], 'Contact')
        self.assertEqual(res_tray_menu[2]['description'], 'Personal settings')
        self.assertEqual(res_tray_menu[3]['description'], 'Redaction')
        self.assertEqual(res_tray_menu[4]['description'], 'Administration')

        # List of Articles
        res_articles = response.context['article_list']
        self.assertEqual(len(res_articles), 4)
        self.assertEqual(res_articles[0].header, 'For Board')
        self.assertEqual(res_articles[1].header, 'For Owners and Board')
        self.assertEqual(res_articles[2].header, 'For Owners')
        self.assertEqual(res_articles[3].header, 'For All')

    def test_board_user(self):
        # Login user
        logged_in = self.client.login(username='jiri', password=users['jiri']['password'])
        self.assertEqual(logged_in, True)

        # Article for all
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_all.slug}))
        self.assertEqual(response.status_code, 200)

        # Article for Board
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 200)

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Menu
        res_tray_menu = response.context['tray_menu_items']
        self.assertEqual(len(res_tray_menu), 4)
        self.assertEqual(res_tray_menu[0]['description'], 'Articles')
        self.assertEqual(res_tray_menu[1]['description'], 'Contact')
        self.assertEqual(res_tray_menu[2]['description'], 'Personal settings')
        self.assertEqual(res_tray_menu[3]['description'], 'Redaction')

        # List of Articles
        res_articles = response.context['article_list']
        self.assertEqual(len(res_articles), 4)
        self.assertEqual(res_articles[0].header, 'For Board')
        self.assertEqual(res_articles[1].header, 'For Owners and Board')
        self.assertEqual(res_articles[2].header, 'For Owners')
        self.assertEqual(res_articles[3].header, 'For All')

    def test_owner_user(self):
        # Login user
        logged_in = self.client.login(username='petr', password=users['petr']['password'])
        self.assertEqual(logged_in, True)

        # Article for all
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_all.slug}))
        self.assertEqual(response.status_code, 200)

        # Article for Owners
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_owners.slug}))
        self.assertEqual(response.status_code, 200)

        # Article for Board
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 404)

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Menu
        res_tray_menu = response.context['tray_menu_items']
        self.assertEqual(len(res_tray_menu), 3)
        self.assertEqual(res_tray_menu[0]['description'], 'Articles')
        self.assertEqual(res_tray_menu[1]['description'], 'Contact')
        self.assertEqual(res_tray_menu[2]['description'], 'Personal settings')

        # List of Articles
        res_articles = response.context['article_list']
        self.assertEqual(len(res_articles), 3)
        self.assertEqual(res_articles[0].header, 'For Owners and Board')
        self.assertEqual(res_articles[1].header, 'For Owners')
        self.assertEqual(res_articles[2].header, 'For All')

    def test_vendor_user(self):
        # Login user
        logged_in = self.client.login(username='karel', password=users['karel']['password'])
        self.assertEqual(logged_in, True)

        # Article for all
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_all.slug}))
        self.assertEqual(response.status_code, 200)

        # Article for Owners
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_owners.slug}))
        self.assertEqual(response.status_code, 404)

        # Article for Board
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 404)

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Menu
        res_tray_menu = response.context['tray_menu_items']
        self.assertEqual(len(res_tray_menu), 3)
        self.assertEqual(res_tray_menu[0]['description'], 'Articles')
        self.assertEqual(res_tray_menu[1]['description'], 'Contact')
        self.assertEqual(res_tray_menu[2]['description'], 'Personal settings')

        # List of Articles
        res_articles = response.context['article_list']
        self.assertEqual(len(res_articles), 1)
        self.assertEqual(res_articles[0].header, 'For All')

    def test_anonymous_user(self):
        # Logout user
        self.client.logout()

        # Article for all
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_all.slug}))
        self.assertEqual(response.status_code, 200)

        # Article for Owners
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_owners.slug}))
        self.assertEqual(response.status_code, 404)

        # Article for Board
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 404)

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Menu
        res_tray_menu = response.context['tray_menu_items']
        self.assertEqual(len(res_tray_menu), 2)
        self.assertEqual(res_tray_menu[0]['description'], 'Articles')
        self.assertEqual(res_tray_menu[1]['description'], 'Contact')

        # List of Articles
        res_articles = response.context['article_list']
        self.assertEqual(len(res_articles), 1)
        self.assertEqual(res_articles[0].header, 'For All')

    def test_top_articles(self):
        # Login board user
        logged_in = self.client.login(username='jiri', password=users['jiri']['password'])
        self.assertEqual(logged_in, True)

        # Article for all
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_all.slug}))
        self.assertEqual(response.status_code, 200)

        # Article for Board
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('article', kwargs={'slug': self.article_for_board.slug}))
        self.assertEqual(response.status_code, 200)

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Top Articles
        res_top = response.context['top_articles']
        self.assertEqual(len(res_top), 2)
        self.assertEqual(res_top[0]['article_id'], self.article_for_board.pk)
        self.assertEqual(res_top[0]['total'], 2)
        self.assertEqual(res_top[1]['article_id'], self.article_for_all.pk)
        self.assertEqual(res_top[1]['total'], 1)

        # Login owner user
        logged_in = self.client.login(username='petr', password=users['petr']['password'])
        self.assertEqual(logged_in, True)

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Top Articles
        res_top = response.context['top_articles']
        self.assertEqual(len(res_top), 1)
        self.assertEqual(res_top[0]['article_id'], self.article_for_all.pk)
        self.assertEqual(res_top[0]['total'], 1)

        # Logout user
        self.client.logout()

        # Main page
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

        # Top Articles
        res_top = response.context['top_articles']
        self.assertEqual(len(res_top), 1)
        self.assertEqual(res_top[0]['article_id'], self.article_for_all.pk)
        self.assertEqual(res_top[0]['total'], 1)

    def test_send_article_notifications(self):
        # Login board user
        logged_in = self.client.login(username='jiri', password=users['jiri']['password'])
        self.assertEqual(logged_in, True)

        # Send notifications for article not published
        response = self.client.get(
            reverse('redaction_article_notifications', kwargs={'pk': self.article_not_published.pk})
        )
        self.assertEqual(response.status_code, 200)
        res_recipients = response.context['object_list']
        self.assertEqual(len(res_recipients), 0)

        # Send notifications for no one
        response = self.client.get(
            reverse('redaction_article_notifications', kwargs={'pk': self.article_for_no_one.pk})
        )
        self.assertEqual(response.status_code, 200)
        res_recipients = response.context['object_list']
        self.assertEqual(len(res_recipients), 0)

        # Send notifications for all
        response = self.client.get(reverse('redaction_article_notifications', kwargs={'pk': self.article_for_all.pk}))
        self.assertEqual(response.status_code, 200)
        res_recipients = response.context['object_list']
        self.assertEqual(len(res_recipients), 4)
        self.assertEqual(res_recipients[0].last_name, 'Beran')
        self.assertEqual(res_recipients[1].last_name, 'Brambůrek')
        self.assertEqual(res_recipients[2].last_name, 'Lukáš')
        self.assertEqual(res_recipients[3].last_name, 'Nebus')

        # Send notifications for owners
        response = self.client.get(
            reverse('redaction_article_notifications', kwargs={'pk': self.article_for_owners.pk})
        )
        self.assertEqual(response.status_code, 200)
        res_recipients = response.context['object_list']
        self.assertEqual(len(res_recipients), 3)
        self.assertEqual(res_recipients[0].last_name, 'Beran')
        self.assertEqual(res_recipients[1].last_name, 'Brambůrek')
        self.assertEqual(res_recipients[2].last_name, 'Nebus')

        # Send notifications for board
        response = self.client.get(
            reverse('redaction_article_notifications', kwargs={'pk': self.article_for_board.pk})
        )
        self.assertEqual(response.status_code, 200)
        res_recipients = response.context['object_list']
        self.assertEqual(len(res_recipients), 2)
        self.assertEqual(res_recipients[0].last_name, 'Beran')
        self.assertEqual(res_recipients[1].last_name, 'Brambůrek')

        # Send notifications for board
        response = self.client.get(
            reverse('redaction_article_notifications', kwargs={'pk': self.article_for_owners_and_board.pk})
        )
        self.assertEqual(response.status_code, 200)
        res_recipients = response.context['object_list']
        self.assertEqual(len(res_recipients), 3)
        self.assertEqual(res_recipients[0].last_name, 'Beran')
        self.assertEqual(res_recipients[1].last_name, 'Brambůrek')
        self.assertEqual(res_recipients[2].last_name, 'Nebus')
