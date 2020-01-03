from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from rules.contrib.models import RulesModel

from commissions import rules
import rules as baseRules
from users.models import User


class Tag(models.Model):
    """
    Les tags associable aux commissions pour les trier et les retrouver
    """
    # Le nom du tag
    name = models.CharField(max_length=100)

    # Le nom du tag modifié pour tenir dans une URL
    slug = models.SlugField(unique=True, blank=True)

    # Couleur du tag
    color = models.CharField(max_length=20)

    # Si le champ est en rapport avec le sport pour inciter à prendre une adhésion au BDS
    sport_related = models.BooleanField(default=False, help_text="Le tag est en rapport avec du sport, les utilisateurs seront encouragés à adhèrer au BDS")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Commission(RulesModel):
    """
    Le modèle contant toutes les informations d'une commission
    """

    # La commission est elle active et maintenue ?
    is_active = models.BooleanField(default=True)

    # Le nom de la commission
    name = models.CharField(max_length=30)

    # Le nom de la commission modifié pour qu'il soit valide dans une URL
    slug = models.SlugField(unique=True, blank=True)

    # Une courte description de la commission en quelques mots
    short_description = models.CharField(max_length=60)

    # Une longue description formattée en Markdown
    description = models.TextField()

    # Le logo de la commission
    logo = models.ImageField(upload_to="commission/logos")

    # La banière de la commission
    banner = models.ImageField(upload_to="commission/banners", blank=True, null=True)

    # L'utilisateur qui possède le rôle de président de la commission
    president = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='president_commissions')

    # L'utilisateur qui possède le rôle de trésorier de la commission
    treasurer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='treasurer_commissions')

    # L'utilisateur qui possède le rôle de suppléant de la commission
    deputy = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='deputy_commissions')

    # La date de creation de la commission
    creation_date = models.DateTimeField(auto_now_add=True)

    # La date de dissolution de la commission
    end_date = models.DateTimeField(default=None, blank=True, null=True)

    # Les tags de la commission
    tags = models.ManyToManyField(Tag, blank=True, related_name='tags_commissions')

    # L'organisation en charge de la gestion de la commission (BDE ou BDS)
    organization_dependant = models.CharField(max_length=100, choices=[("bde", "BDE"), ("bds", "BDS")], default="bde", help_text="L'organisation à laquelle appartiens la commission")

    # Si la "commission" est un organisation, c'est a dire qu'elle n'apparait pas sur le liste des commission mais peut profiter de toutes les fonctionnalités des commissions comme les events, les hashtags, etc..
    is_organization = models.BooleanField(default=False, help_text="Définie que cet instance est une organisation et non une commission, une organisation n'apparait pas dans la liste des commissions mais dispose de toutes les fonctionnalités associés")

    def save(self, *args, **kwargs):
        if self.slug is None or self.slug == "":
            self.slug = slugify(self.name)

        super(Commission, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def has_team_member(self, request):
        return ((
            request.user.get_username() == self.president.get_username()
        ) or (
            request.user.get_username() == self.treasurer.get_username()
        ) or (
            self.deputy is not None and request.user.get_username() == self.deputy.get_username()
        ))

    def has_change_permission(self, request):
        return self.is_active and self.has_team_member(request)

    def has_change_members_permission(self, request):
        return self.is_active and request.user.get_username() == self.president.get_username()

    def in_commission_membre(self, request):
        for membre in MembreCommission.objects.filter(commission = self) :
            if(request.user.get_username() == membre.identification.get_username()):
                return self.is_active
        return False

    def get_membres(self):
        return MembreCommission.objects.filter(commission = self)

    def has_add_event_permission(self, request):
        return self.has_change_permission(request)

    class Meta:

        rules_permissions = {

            "view":             baseRules.always_allow,

            "change":           baseRules.is_active &
                                  baseRules.is_authenticated &
                                  rules.is_active_commission &
                                  rules.is_commission_team_member,

            "change_members":   rules.is_active_commission &
                                  rules.is_commission_president,

        }


class MembreCommission(models.Model):
    """
    Les membre de commission commissions
    """
    # L'ID du membre
    identification = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='membre_identification')
    commission = models.ForeignKey(Commission, on_delete=models.SET_NULL, null=True, related_name='membre_commission')
    join_date = models.DateTimeField(auto_now_add=True)

    # Les permissions du membre (TODO)
    role = models.CharField(max_length=50, default=None, null=True, blank=True)

    def __str__(self):
        return self.identification.email + (" ( " + self.role + " )") if self.role is not None else ""


class Event(models.Model):
    """
    Les évènements créés par les commissions
    """
    # Le nom de l'évènement
    name = models.CharField(max_length=100)

    # Le nom du tag modifié pour tenir dans une url
    slug = models.SlugField(unique=True, blank=True)

    # La description de l'évènement
    description = models.TextField()

    # Emplacement de l'événement
    location = models.CharField(max_length=255, blank=True, null=True)

    # Photo de l'évènement
    banner = models.ImageField(upload_to="events/photos", blank=True, null=True)

    # Commission liée à l'évènement
    commission = models.ForeignKey(Commission, on_delete=models.SET_NULL, null=True, related_name='events')

    # La date de creation de l'évènement
    creation_date = models.DateTimeField(auto_now_add=True)

    # La date de dernière mise à jour de l'évènement
    update_date = models.DateTimeField(auto_now=True)

    # La date de début l'évènement
    event_date_start = models.DateTimeField()

    # La date de fin de l'évènement
    event_date_end = models.DateTimeField()

    def get_start_utc(self):
        return self.event_date_start - timedelta(hours=1)

    def get_end_utc(self):
        return self.event_date_end - timedelta(hours=1)

    def has_started(self):
        return self.event_date_start < timezone.now() and self.event_date_end > timezone.now()

    def has_ended(self):
        return self.event_date_end < timezone.now()

    def has_change_event_permission(self, request):
        return self.commission.has_change_permission(request)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):

    date = models.DateTimeField(help_text="Date de publication du post")

    content = models.CharField(max_length=280)

    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name="posts")

    source = models.CharField(max_length=50, choices=[
        ('internal', 'Système interne'),
        ('twitter', 'Twitter')
    ], default="internal", help_text="Provenance du post")

    external_id = models.CharField(max_length=255, null=True, blank=True, help_text="Identifiant du post sur le site externe (Twitter, Instagram, etc...)")

    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True)

    author_text = models.CharField(max_length=50, help_text="Texte alternatif de l'auteur dans le cas où l'utilisateur soit Null")

    author_image = models.CharField(max_length=255, blank=True, null=True, help_text="URL d'image de profil de l'auteur dans le cas ou l'utilisateur est null")

    is_moderated = models.BooleanField(help_text="Si le poste est modéré et masqué aux utilisateurs", default=False)

    def has_even_medias(self):
        return self.images.all().count() % 2 == 0

    def __str__(self):
        return "Post de {} le {}".format(self.author if self.author is not None else self.author_text, self.date)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.date is None:
            self.date = timezone.now()
        return super().save(force_insert, force_update, using, update_fields)


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="posts/images")


def quester_query_validator(value):
    if value[0] != "#" and value[0] != "@":
        raise ValidationError('{} is not a valid query, must begin with # or @'.format(value))
    if " " in value:
        raise ValidationError('{} is not a valid query, must not contain space'.format(value))


class CommissionSocialQuester(models.Model):
    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name="social_questers")
    query = models.CharField(max_length=50, validators=[quester_query_validator])
    since_date = models.DateTimeField()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.since_date is None:
            self.since_date = timezone.now()
        return super().save(force_insert, force_update, using, update_fields)
