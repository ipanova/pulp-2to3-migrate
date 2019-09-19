from django.db import models

from pulpcore.app.models import Content  # it has to be imported directly from pulpcore see #5353
from pulpcore.plugin.models import Model


class Pulp2Content(Model):
    """
    General info about Pulp 2 content.

    Pulp3 plugin models should create a Foreign key to this model.

    Fields:
        pulp2_id (models.CharField): Content ID in Pulp 2
        pulp2_content_type_id (models.CharField): Content type in Pulp 2
        pulp2_last_updated (models.PositiveIntegerField): Content creation or update time in Pulp 2
        pulp2_storage_path (models.TextField): Content storage path on Pulp 2 system
        downloaded (models.BooleanField): Flag to identify if content is on a filesystem or not

    Relations:
        pulp3_content (models.ForeignKey): Pulp 3 content which Pulp 2 content was migrated to
    """

    @property
    def detail_model(self):
        return getattr(self, '%s_detail_model' % self.pulp2_content_type_id).get()

    pulp2_id = models.CharField(max_length=255)
    pulp2_content_type_id = models.CharField(max_length=255)
    pulp2_last_updated = models.PositiveIntegerField()
    pulp2_storage_path = models.TextField(null=True) # what about content without storage_path
    downloaded = models.BooleanField(default=True)
    pulp3_content = models.ForeignKey(Content, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('pulp2_id', 'pulp2_content_type_id')


class Pulp2to3Content(Model):
    """
    Pulp 2to3 detail content model to store pulp 2 content details for Pulp 3 content creation.
    """
    pulp2content = models.ForeignKey(Pulp2Content,
                                     on_delete=models.CASCADE)
    type = '<your pulp 2 content type>'

    class Meta:
        abstract = True

    @classmethod
    async def pre_migrate_content_detail(cls, content_batch):
        """
        Pre-migrate Pulp 2 content with all the fields needed to create a Pulp 3 Content

        Args:
             content_batch(list of Pulp2Content): pre-migrated generic data for Pulp 2 content.

        Example for ISO content:
        >>> pulp2_map = {pulp2content.pulp2_id: pulp2content for pulp2content in content_batch}
        >>> pulp2_ids = pulp2_id_obj_map.keys()
        >>> pulp2_iso_content_batch = ISO.objects.filter(id__in=pulp2_ids)
        >>> pulp2iso_to_save = [Pulp2ISO(name=iso.name,
        >>>                              checksum=iso.checksum,
        >>>                              size=iso.size,
        >>>                              pulp2content=pulp2_map[iso.id])
        >>>                     for iso in pulp2_iso_content_batch]
        >>> cls.objects.bulk_create(pulp2iso_to_save, ignore_conflicts=True)
        """
        raise NotImplementedError()

    @classmethod
    async def migrate_content_to_pulp3(cls):
        """
        Migrate pre-migrated Pulp 2 content.

        Create a DeclatativeContentMigration pipeline here and instantiate it with your first stage.
        Here the default implementation of the first stage is used:
        >>> first_stage = ContentMigrationFirstStage(cls)
        >>> dv = DeclarativeContentMigration(first_stage=first_stage)
        >>> await dv.create()
        """
        raise NotImplementedError()

    def create_pulp3_content(self):
        """
        Create a Pulp 3 detail Content unit for saving it later in a bulk operation.

        Return an unsaved Pulp 3 Content
        """
        raise NotImplementedError()
