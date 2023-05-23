from pydantic import BaseModel, validator, ValidationError

from typing import List, Tuple, Union

from bloqade.submission.ir.task_results import (
    QuEraShotResult,
    QuEraTaskResults,
)


class SiteClusterInfo(BaseModel):
    """Class that stores the mapping of batched jobs.

    Args:
        cluster_index (int): the index of the cluster a site belongs to
        global_site_index (int): the index of the site in the multplexed system
        local_site_index (int): the index of the site in the original system
    """

    cluster_index: Tuple[int, int]
    global_site_index: int
    local_site_index: int


class ParallelDecoder(BaseModel):
    mapping: List[SiteClusterInfo]
    sites_per_cluster: int
    number_of_cluster: int

    def __init__(self, mapping: List[SiteClusterInfo]):
        local_site_indices = set()
        cluster_indices = set()

        for site in mapping:
            local_site_indices.add(site.local_site_index)
            cluster_indices.add(site.cluster_index)

        super().__init__(
            mapping=mapping,
            sites_per_cluster=len(local_site_indices),
            number_of_cluster=len(cluster_indices),
        )

    # should work if we go to the coordinate-based indexing system
    @validator("mapping")
    def sites_belong_to_unqiue_cluster(cls, mapping):
        sites = [ele.global_site_index for ele in mapping]
        unique_sites = set(sites)
        if len(sites) != len(unique_sites):
            raise ValidationError("one or more sites mapped to multiple clusters")

        return mapping

    # map individual atom indices (in the context of the ENTIRE geometry)
    # to the cluster-specific indices:
    # {}
    def get_site_indices(self):
        site_indices = {}
        for site_cluster in self.mapping:  # iterate through global_site_index
            global_site_index = site_cluster.global_site_index
            local_site_index = site_cluster.local_site_index
            site_indices[global_site_index] = local_site_index

        return site_indices

    # should work if we go to coordinate-based indexing
    # map each cluster index to the global index
    def get_cluster_indices(self):
        site_indices = self.get_site_indices()

        cluster_indices = {}
        for site_cluster in self.mapping:
            global_site_index = site_cluster.global_site_index
            cluster_index = site_cluster.cluster_index

            cluster_indices[cluster_index] = cluster_indices.get(cluster_index, []) + [
                global_site_index
            ]

        return {
            cluster_index: sorted(sites, key=lambda site: site_indices[site])
            for cluster_index, sites in cluster_indices.items()
        }

    def decode_results(
        self, task_result: QuEraTaskResults, clusters: Union[int, List[int]] = []
    ) -> QuEraTaskResults:
        cluster_indices = self.get_cluster_indices()

        shot_outputs = []

        match clusters:
            case int(cluster_index):
                clusters = [cluster_index]
            case list() if clusters:
                pass
            case _:
                clusters = cluster_indices.keys()

        for full_shot_result in task_result.shot_outputs:
            for cluster_site_indices in cluster_indices.values():
                shot_outputs.append(
                    QuEraShotResult(
                        shot_status=full_shot_result.shot_status,
                        pre_sequence=[
                            full_shot_result.pre_sequence[index]
                            for index in cluster_site_indices
                        ],
                        post_sequence=[
                            full_shot_result.post_sequence[index]
                            for index in cluster_site_indices
                        ],
                    )
                )

        return QuEraTaskResults(
            task_status=task_result.task_status, shot_outputs=shot_outputs
        )
