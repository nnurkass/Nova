"""
GraphQL query strings for the goszakup.gov.kz v3 API.

Contains standard GraphQL queries for:
- Search announcements / tenders by filter
- Get announcement and lot details
- Get customer information
"""

SEARCH_ANNOUNCEMENTS = """
query SearchAnnouncements(
    $filter: TrdAnnouncementFilterInput,
    $limit: Int,
    $after: Int
) {
    TrdBuy(filter: $filter, limit: $limit, after: $after) {
        id
        numberAnno
        nameRu
        nameKz
        statusId
        refBuyTypeId
        orgBin
        orgNameRu
        totalSum
        publishDate
        startDate
        endDate
        customerBin
        customerNameRu
        refRegionId
        Lots {
            id
            lotNumber
            nameRu
            nameKz
            amount
            count
            unit
        }
    }
}
"""

GET_ANNOUNCEMENT_DETAIL = """
query GetAnnouncementDetail($id: Int!) {
    TrdBuy(filter: { id: $id }) {
        id
        numberAnno
        nameRu
        nameKz
        statusId
        refBuyTypeId
        orgBin
        orgNameRu
        totalSum
        publishDate
        startDate
        endDate
        customerBin
        customerNameRu
        refRegionId
        descriptionRu
        Lots {
            id
            lotNumber
            nameRu
            nameKz
            amount
            count
            unit
            descriptionRu
            Files {
                id
                name
                filePath
            }
        }
    }
}
"""

GET_LOTS = """
query GetLots($announcementId: Int!) {
    Lots(filter: { trdBuyId: $announcementId }) {
        id
        lotNumber
        nameRu
        nameKz
        amount
        count
        unit
    }
}
"""

__all__ = [
    "SEARCH_ANNOUNCEMENTS",
    "GET_ANNOUNCEMENT_DETAIL",
    "GET_LOTS",
]
