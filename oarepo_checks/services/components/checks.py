from invenio_checks.api import ChecksAPI
from invenio_checks.components import toggle_on_feature_flag
from invenio_drafts_resources.services.records.components import ServiceComponent


@toggle_on_feature_flag
class ChecksOnCreateComponent(ServiceComponent):
    """Custom checks component to run checks also on creation of a record."""

    def create(self, identity, data=None, record=None, **kwargs):
        """Run checks on draft create."""
        draft = record  # rename for clarity

        # Take into account already included communities
        community_ids = self._get_record_communities(draft)

        past_runs = ChecksAPI.get_runs(draft)
        for run in past_runs:
            community_ids.add(str(run.config.community_id))

        updated_runs = []
        configs = ChecksAPI.get_configs(community_ids)
        for config in configs:
            run = ChecksAPI.run_check(config, draft, self.uow)
            if run:
                updated_runs.append(run)
