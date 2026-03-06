"""GraphQL query constants for the goszakup.gov.kz v3 API."""

SEARCH_ANNOUNCEMENTS = """
query SearchAnnouncements($filter: TrdBuyFiltersInput, $limit: Int) {
  TrdBuy(filter: $filter, limit: $limit) {
    id
    numberAnno
    nameRu
    nameKz
    totalSum
    refTradeMethodsId
    refBuyStatusId
    customerBin
    customerNameRu
    customerNameKz
    orgPid
    orgBin
    orgNameRu
    orgNameKz
    publishDate
    startDate
    endDate
    kato
    Files {
      id
      filePath
      originalName
      nameRu
      nameKz
    }
  }
}
""".strip()

GET_ANNOUNCEMENT_DETAIL = """
query GetAnnouncementDetail($filter: TrdBuyFiltersInput, $limit: Int) {
  TrdBuy(filter: $filter, limit: $limit) {
    id
    numberAnno
    nameRu
    nameKz
    totalSum
    refTradeMethodsId
    refBuyStatusId
    customerBin
    customerNameRu
    customerNameKz
    orgPid
    orgBin
    orgNameRu
    orgNameKz
    publishDate
    startDate
    endDate
    kato
    RefBuyStatus {
      id
      code
      nameRu
    }
    RefTradeMethods {
      id
      nameRu
    }
    Files {
      id
      filePath
      originalName
      nameRu
      nameKz
    }
  }
}
""".strip()

GET_LOTS = """
query GetLots($filter: LotsFiltersInput, $limit: Int) {
  Lots(filter: $filter, limit: $limit) {
    id
    lotNumber
    nameRu
    nameKz
    descriptionRu
    descriptionKz
    amount
    count
    customerBin
    customerNameRu
    customerNameKz
    trdBuyId
    refTradeMethodsId
    Files {
      id
      filePath
      originalName
      nameRu
      nameKz
    }
  }
}
""".strip()

GET_CONTRACTS = """
query GetContracts($filter: ContractFiltersInput, $limit: Int) {
  Contract(filter: $filter, limit: $limit) {
    id
    trdBuyId
    trdBuyNumberAnno
    contractNumber
    refContractStatusId
    supplierBiin
    signDate
    crdate
    contractSum
    Files {
      id
      filePath
      originalName
      nameRu
      nameKz
    }
  }
}
""".strip()

__all__ = [
    "GET_ANNOUNCEMENT_DETAIL",
    "GET_CONTRACTS",
    "GET_LOTS",
    "SEARCH_ANNOUNCEMENTS",
]
