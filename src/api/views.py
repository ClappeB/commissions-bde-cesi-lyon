from elasticsearch_dsl.query import MultiMatch
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, schema, action
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from url_filter.integrations.drf import DjangoFilterBackend

from api.serializers import UserSerializer, CommissionSerializer, PostSerializer, SocialQuesterSerializer, \
    PostImageSerializer, UploadSerializer, UploadCreateSerializer, MixedSearchSerializer, EventSerializer
from commissions.documents import CommissionDocument, EventDocument
from commissions.models import Commission, Post, CommissionSocialQuester, PostImage, Event
from documentation.documents import DocumentationDocument
from documents.models import Upload
from index.documents import QuickLinkDocument
from users.documents import UserDocument
from users.models import User


class UserViewSet(viewsets.ModelViewSet):
    """
	Permet de rechercher/ajouter/modifier les Utilisateurs du site

	Un utilisateur peut être un étudiant du CESI (connecté avec un compte Viacesi), une personne n'ayant pas de compte viacesi ou un utiiisateur "fictif" utilisé par une application par exemple.
	Tout les étudiants du CESI ne sont pas inscrit de base mais sont onscrit lors de leur première connexion.
	"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions]
    filter_backends = [DjangoFilterBackend]
    filter_fields = [
        "id",
        "email",
        "support_member"
    ]


class CommissionViewSet(viewsets.ModelViewSet):
    """
	Permet de rechercher/ajouter/modifier/supprimer les Commissions du site

	Une commission est une entité du BDE qui dispose d'un conseil d'administration, qui peux organiser des événements, être financée par le BDE et bien d'autres actions.
	Ce sont les clubs de la vie associative du CESI

	**NOTE** : Les commissions ayant le champ `is_organization` sont des *organisations* et ne doivent pes être considérées comme des commissions standards. Elle représentent des strucutres ayant les mêmes fonctionnalités que les commissions mais n'ètant pas reconnues légalement comme êtant des commiession.
	Exemple : Le BDE lui même dispose d'une "commission" à son nom pour l'oganisation es événements et our profiter de toutes les consonnalités du site.
	"""

    queryset = Commission.objects.all()
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions]
    filter_backends = [DjangoFilterBackend]
    filter_fields = [
        "id",
        "is_active",
        "name",
        "slug",
        "short_description",
        "description",
        "president",
        "treasurer",
        "deputy",
        "creation_date",
        "end_date",
        "organization_dependant",
        "social_questers",
        "is_organization"
    ]


class EventViewSet(viewsets.ModelViewSet):
    """
	Permet de rechercher/ajouter/modifier/supprimer les événements du site
	"""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions]
    filter_backends = [DjangoFilterBackend]
    filter_fields = [
        "id",
        "name",
        "slug",
        "description",
        "location",
        "banner",
        "commission",
        "creation_date",
        "update_date",
        "event_date_start",
        "event_date_end"
    ]


class PostViewSet(viewsets.ModelViewSet):
    """
	Permet de rechercher/ajouter/modifier/supprimer les Posts du site

	Un post est une publication présente dans le fil d'actualité du BDE sur la page d'accueil.
	Chaque post est associé à une commissions et peut disposer d'une source définissant l'emplacement d'origine du post.
	Les posts sont automatiquement créé lors de la publication, sur un réseau social, d'une publication matchant les paramètres d'un SocialQuester.
	"""

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions]
    filter_backends = [DjangoFilterBackend]
    filter_fields = [
        "id",
        "content",
        "source",
        "external_id",
        "author",
        "author_text",
        "commission",
        "date",
        "is_moderated"
    ]


class SocialQuesterViewSet(viewsets.ModelViewSet):
    """
	Permet de rechercher/ajouter/modifier/supprimer les SocialQuesters du site

	Un SocialQuester est une règle de recherche de posts sur les réseaux sociaux.
	Un sous-système du site est en charge de vérifier la publication de certains posts en se basant sur les rêgles des social quester.
	Si une publication est en accord avec les rêgles définies dans le SocialQuester, un post est créé sur le site et apparaitra dans le fil d'actualité général et de la commissions associée.
	"""
    queryset = CommissionSocialQuester.objects.all()
    serializer_class = SocialQuesterSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions]
    filter_backends = [DjangoFilterBackend]
    filter_fields = [
        "id",
        "commission",
        "query",
        "since_date"
    ]


class PostImagesViewSet(viewsets.ModelViewSet):
    """
	Permet de rechercher/ajouter/modifier/supprimer les Images des posts du site
	"""

    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions]
    filter_backends = [DjangoFilterBackend]
    filter_fields = [
        "id",
        "post"
    ]


class UploadViewSet(viewsets.ModelViewSet):
    """
	Permet de rechercher/ajouter/modifier/supprimer les Uploads utilisateurs du site

	Au travers des champs Markdown, les utilisateurs du site peuvent uploader des médias pour les intègrer dans leurs descriptions.
	"""
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, DjangoObjectPermissions]

    def create(self, request, *args, **kwargs):
        """
		Permet d'uploader un nouveau média utilisateur

        Au travers des champs Markdown, les utilisateurs du site peuvent uploader des médias pour les intègrer dans leurs descriptions.

		**NOTE** : Les données envoyées doivent impérativement être envoyés via un `multipart/form-data` pour que l'upload fonctionne convenablement sur le champ `file`.
		"""
        serializer = UploadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)

        full_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(full_serializer.data)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MixedSearch(APIView):
    """
    Recherche sur l'ensemble du site internet
    """

    def get(self, request, format=None):
        """
        Effectue une recherche sur l'ensemble des données du site web

        **NOTE** : Un paramètre `q` et requis pour définir la requète à éfféctuer.
        """

        if not "q" in request.GET:
            return Response({"error": "Provide a `q` GET parameter"}, status=status.HTTP_400_BAD_REQUEST)

        query = request.GET['q']

        commissions = CommissionDocument.search().query(MultiMatch(query=query,
                                                                   tie_breaker=0.3,
                                                                   fuzziness=1,
                                                                   fields=[
                                                                       "name^3",
                                                                       "short_description^2",
                                                                       "description",
                                                                       "organization_dependant",
                                                                       "tags^3"
                                                                   ]))

        users = UserDocument.search().query(MultiMatch(query=query,
                                                       tie_breaker=0.3,
                                                       fuzziness=1,
                                                       fields=[
                                                           "email",
                                                           "first_name^2",
                                                           "last_name^2"
                                                       ]))

        events = EventDocument.search().query(MultiMatch(query=query,
                                                         tie_breaker=0.3,
                                                         fuzziness=1,
                                                         fields=[
                                                             "name^2",
                                                             "location^2",
                                                             "description",
                                                             "commission"
                                                         ]))

        quicklinks = QuickLinkDocument.search().query(MultiMatch(query=query,
                                                                 tie_breaker=0.3,
                                                                 fuzziness=1,
                                                                 fields=[
                                                                     "text^2",
                                                                     "url",
                                                                 ]))

        documentation = DocumentationDocument.search().query(MultiMatch(query=query,
                                                                 tie_breaker=0.3,
                                                                 fuzziness=1,
                                                                 fields=[
                                                                     "title^3",
                                                                     "content^2",
                                                                     "path"
                                                                 ])).execute()

        serializer = MixedSearchSerializer({
            "commissions": commissions.to_queryset(),
            "documentations": documentation.hits,
            "users": users.to_queryset(),
            "events": events.to_queryset(),
            "quicklinks": quicklinks.to_queryset(),
        }, context={'request': request})

        return Response(serializer.data)
