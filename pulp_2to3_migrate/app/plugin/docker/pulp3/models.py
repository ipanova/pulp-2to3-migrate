from django.db import models
from django.contrib.postgres.fields import ArrayField

from pulp_2to3_migrate.app.models import Pulp2to3Content
from pulp_2to3_migrate.app.plugin.api import (
    ContentMigrationFirstStage,
    DockerContentMigrationFirstStage,
    DeclarativeContentMigration,
    DockerDeclarativeContentMigration,
)

from pulp_2to3_migrate.app.plugin.docker.pulp2 import models as pulp2_models

from pulp_docker.constants import MEDIA_TYPE
from pulp_docker.app.models import Blob, Manifest, Tag


class Pulp2Blob(Pulp2to3Content):
    """
    Pulp 2to3 detail content model to store pulp 2 Blob content details for Pulp 3 content creation.
    """
    digest = models.CharField(max_length=255)
    media_type = models.CharField(max_length=80)

    type = 'docker_blob'
    checksum_type = 'sha256'

    class Meta:
        unique_together = ('digest', 'pulp2content')
        default_related_name = 'docker_blob_detail_model'

    @property
    def expected_digests(self):
        return {self.checksum_type: self.digest.split(':')[1]}

    @property
    def expected_size(self):
        return 

    @property
    def relative_path_for_content_artifact(self):
        return self.digest

    @classmethod
    async def pre_migrate_content_detail(cls, content_batch):
        """
        Pre-migrate Pulp 2 Blob content with all the fields needed to create a Pulp 3 FileContent

        Args:
             content_batch(list of Pulp2Content): pre-migrated generic data for Pulp 2 content.

        """
        # TODO: all pulp2content objects from the batch are in memory. Concerns?
        pulp2_id_obj_map = {pulp2content.pulp2_id: pulp2content for pulp2content in content_batch}
        pulp2_ids = pulp2_id_obj_map.keys()
        pulp2_blob_content_batch = pulp2_models.Blob.objects.filter(id__in=pulp2_ids)
        pulp2blob_to_save = [Pulp2Blob(digest=blob.digest,
                                       media_type=MEDIA_TYPE.REGULAR_BLOB,
                                       pulp2content=pulp2_id_obj_map[blob.id])
                            for blob in pulp2_blob_content_batch]
        cls.objects.bulk_create(pulp2blob_to_save, ignore_conflicts=True)

    @classmethod
    async def migrate_content_to_pulp3(cls):
        """
        Migrate pre-migrated Pulp 2 docker content.
        """
        first_stage = DockerContentMigrationFirstStage(cls)
        dv = DockerDeclarativeContentMigration(first_stage=first_stage)
        await dv.create()

    def create_pulp3_content(self):
        """
        Create a Pulp 3 Blob unit for saving it later in a bulk operation.
        """
        return Blob(digest=self.digest, media_type=self.media_type)


class Pulp2Manifest(Pulp2to3Content):
    """
    Pulp 2to3 detail content model to store pulp 2 Manifest content details for Pulp 3 content creation.
    """
    digest = models.CharField(max_length=255)
    schema_version = models.IntegerField()
    media_type = models.CharField(max_length=80)
    blobs = ArrayField(models.CharField(max_length=255))
    config_blob = models.CharField(max_length=255, null=True)

    type = 'docker_manifest'
    checksum_type = 'sha256'

    class Meta:
        unique_together = ('digest', 'pulp2content')
        default_related_name = 'docker_manifest_detail_model'

    @property
    def expected_digests(self):
        # TODO digest is different if it is a schema1, remove signatures from payload calculation
        return {self.checksum_type: self.digest.split(':')[1]}

    @property
    def expected_size(self):
        return

    @property
    def relative_path_for_content_artifact(self):
        return self.digest

    @classmethod
    async def pre_migrate_content_detail(cls, content_batch):
        """
        Pre-migrate Pulp 2 Manifest content with all the fields needed to create a Pulp 3 Manifest

        Args:
             content_batch(list of Pulp2Content): pre-migrated generic data for Pulp 2 content.

        """
        # TODO: all pulp2content objects from the batch are in memory. Concerns?
        pulp2_id_obj_map = {pulp2content.pulp2_id: pulp2content for pulp2content in content_batch}
        pulp2_ids = pulp2_id_obj_map.keys()
        pulp2_m_content_batch = pulp2_models.Manifest.objects.filter(id__in=pulp2_ids)
        pulp2m_to_save = [Pulp2Manifest(digest=m.digest,
                                        media_type = MEDIA_TYPE.MANIFEST_V2 if m.schema_version==2 else MEDIA_TYPE.MANIFEST_V1,
                                        schema_version = m.schema_version,
                                        config_blob = m.config_layer,
                                        blobs = [layer.blob_sum for layer in m.fs_layers if layer.layer_type != MEDIA_TYPE.FOREIGN_BLOB],
                                        pulp2content=pulp2_id_obj_map[m.id])
                            for m in pulp2_m_content_batch]
        cls.objects.bulk_create(pulp2m_to_save, ignore_conflicts=True)

    @classmethod
    async def migrate_content_to_pulp3(cls):
        """
        Migrate pre-migrated Pulp 2 docker content.
        """
        first_stage = DockerContentMigrationFirstStage(cls)
        dv = DockerDeclarativeContentMigration(first_stage=first_stage)
        await dv.create()


    def create_pulp3_content(self):
        """
        Create a Pulp 3 FileContent unit for saving it later in a bulk operation.
        """
        # find saved blobs create BlobManifest
        return Manifest(digest=self.digest, media_type=self.media_type, schema_version = self.schema_version)


class Pulp2ManifestList(Pulp2to3Content):
    """
    Pulp 2to3 detail content model to store pulp 2 Manifest content details for Pulp 3 content creation.
    """
    digest = models.CharField(max_length=255)
    media_type = models.CharField(max_length=80)
    schema_version = models.IntegerField()
    media_type = models.CharField(max_length=80)
    listed_manifests = ArrayField(models.CharField(max_length=255))

    type = 'docker_manifest_list'
    checksum_type = 'sha256'

    class Meta:
        unique_together = ('digest', 'pulp2content')
        default_related_name = 'docker_manifest_list_detail_model'

    @property
    def expected_digests(self):
        return {self.checksum_type: self.digest.split(':')[1]}

    @property
    def expected_size(self):
        return

    @property
    def relative_path_for_content_artifact(self):
        return self.digest

    @classmethod
    async def pre_migrate_content_detail(cls, content_batch):
        """
        Pre-migrate Pulp 2 ISO content with all the fields needed to create a Pulp 3 FileContent

        Args:
             content_batch(list of Pulp2Content): pre-migrated generic data for Pulp 2 content.

        """
        # TODO: all pulp2content objects from the batch are in memory. Concerns?
        pulp2_id_obj_map = {pulp2content.pulp2_id: pulp2content for pulp2content in content_batch}
        pulp2_ids = pulp2_id_obj_map.keys()
        pulp2_m_content_batch = pulp2_models.ManifestList.objects.filter(id__in=pulp2_ids)
        pulp2m_to_save = [Pulp2ManifestList(digest=m.digest,
                                        media_type = MEDIA_TYPE.MANIFEST_LIST,
                                        schema_version = m.schema_version,
                                        listed_manifests = [manifest.digest for manifest in m.manifests],
                                        pulp2content=pulp2_id_obj_map[m.id])
                            for m in pulp2_m_content_batch]
        cls.objects.bulk_create(pulp2m_to_save, ignore_conflicts=True)

    @classmethod
    async def migrate_content_to_pulp3(cls):
        """
        Migrate pre-migrated Pulp 2 docker content.
        """
        first_stage = DockerContentMigrationFirstStage(cls)
        dv = DockerDeclarativeContentMigration(first_stage=first_stage)
        await dv.create()

    def create_pulp3_content(self):
        """
        Create a Pulp 3 Manifest unit for saving it later in a bulk operation.
        """
        # find saved manifests and create ManifestListManifest
        # read from ML storage_path
        return Manifest(digest=self.digest, media_type=self.media_type, schema_version = self.schema_version)


class Pulp2Tag(Pulp2to3Content):
    """
    Pulp 2to3 detail content model to store pulp 2 Tag content details for Pulp 3 content creation.
    """
    name = models.CharField(max_length=255)
    tagged_manifest = models.CharField(max_length=255)

    type = 'docker_tag'
    checksum_type = 'sha256'

    class Meta:
        unique_together = ('name', 'tagged_manifest', 'pulp2content')
        default_related_name = 'docker_tag_detail_model'

    @property
    def relative_path_for_content_artifact(self):
        return self.name

    @classmethod
    async def pre_migrate_content_detail(cls, content_batch):
        """
        Pre-migrate Pulp 2 Tag content with all the fields needed to create a Pulp 3 Tag

        Args:
             content_batch(list of Pulp2Content): pre-migrated generic data for Pulp 2 content.

        """
        # TODO: all pulp2content objects from the batch are in memory. Concerns?
        pulp2_id_obj_map = {pulp2content.pulp2_id: pulp2content for pulp2content in content_batch}
        pulp2_ids = pulp2_id_obj_map.keys()
        pulp2_tag_content_batch = pulp2_models.Tag.objects.filter(id__in=pulp2_ids)
        pulp2tag_to_save = [Pulp2Tag(name=tag.name,
                                     tagged_manifest = tag.manifest_digest,
                                     pulp2content=pulp2_id_obj_map[tag.id])
                            for tag in pulp2_tag_content_batch]
        cls.objects.bulk_create(pulp2tag_to_save, ignore_conflicts=True)

    @classmethod
    async def migrate_content_to_pulp3(cls):
        """
        Migrate pre-migrated Pulp 2 docker content.
        """
        first_stage = DockerContentMigrationFirstStage(cls)
        dv = DockerDeclarativeContentMigration(first_stage=first_stage)
        await dv.create()


    def create_pulp3_content(self):
        """
        Create a Pulp 3 Tag unit for saving it later in a bulk operation.
        """
        # find saved Manifests
        #return Tag(name=self.name, tagged_manifest=manifest)
        return Tag(name=self.name)
