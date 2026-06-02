// TODO: replace mock data with backend API when the licensing portal backend is built.

export type RequestStatus = "Pending" | "Approved" | "Rejected";
export type ActivationStatus = "Not activated" | "Activated";
export type ReportStatus = "Submitted" | "Draft";
export type InvoiceStatus =
  | "Draft"
  | "Payment Pending"
  | "Payment Submitted"
  | "Under Review"
  | "Payment Complete";
export type LaasVerificationStatus = "Not checked" | "Verified active" | "Needs review";

export type MonthlyReport = {
  month: string;
  broughtForward: number;
  issuedThisMonth: number;
  availableLicenses: number;
  reportedSold: number;
  invoiceQuantity: number;
  carryForward: number;
  reportStatus: ReportStatus;
};

export type LicenseRequest = {
  id: string;
  client: string;
  country: string;
  product: string;
  productVersion: string;
  quantity: number;
  date: string;
  status: RequestStatus;
};

export type LicenseRecord = {
  key: string;
  product: string;
  productVersion: string;
  client: string;
  country: string;
  activationStatus: ActivationStatus;
  issuedDate: string;
  defaultSold: boolean;
  laasVerification: LaasVerificationStatus;
};

export type Invoice = {
  reference: string;
  client: string;
  country: string;
  product: string;
  productVersion: string;
  month: string;
  unitAmount: number;
  totalAmount: number;
  quantity: number;
  status: InvoiceStatus;
};

export type MonthlyHistoryItem = {
  month: string;
  broughtForward: number;
  issuedThisMonth: number;
  availableLicenses: number;
  reportedSold: number;
  invoiceQuantity: number;
  carryForward: number;
};

export type InvoicePreview = {
  reference: string;
  quantity: number;
  status: InvoiceStatus;
};

export const mockClient = "OCULUS";
export const mockClientCountry = "Germany";
export const mockProduct = "OCUMAPS";
export const mockProductVersion = "1.0.0";
export const mockMonth = "June 2026";
export const issuedThisMonth = 10;
export const broughtForward = 0;
export const mockUnitAmount = 120;

export function buildMonthlyReport(reportedSold: number): MonthlyReport {
  const availableLicenses = broughtForward + issuedThisMonth;

  return {
    month: mockMonth,
    broughtForward,
    issuedThisMonth,
    availableLicenses,
    reportedSold,
    invoiceQuantity: reportedSold,
    carryForward: Math.max(availableLicenses - reportedSold, 0),
    reportStatus: "Submitted",
  };
}

export const mockMonthlyReport = buildMonthlyReport(6);

export const mockRequests: LicenseRequest[] = [
  {
    id: "REQ-2026-0061",
    client: mockClient,
    country: mockClientCountry,
    product: mockProduct,
    productVersion: mockProductVersion,
    quantity: 10,
    date: "2026-06-02",
    status: "Pending",
  },
  {
    id: "REQ-2026-0054",
    client: mockClient,
    country: mockClientCountry,
    product: mockProduct,
    productVersion: mockProductVersion,
    quantity: 10,
    date: "2026-05-01",
    status: "Approved",
  },
];

export function buildInvoice(
  quantity: number,
  status: InvoiceStatus = "Draft",
  reference = "Pending",
): Invoice {
  return {
    reference,
    client: mockClient,
    country: mockClientCountry,
    product: mockProduct,
    productVersion: mockProductVersion,
    month: mockMonth,
    unitAmount: mockUnitAmount,
    totalAmount: quantity * mockUnitAmount,
    quantity,
    status,
  };
}

export const mockInvoice = buildInvoice(mockMonthlyReport.invoiceQuantity);

export const mockMonthlyHistory: MonthlyHistoryItem[] = [
  {
    month: "July 2025",
    broughtForward: 0,
    issuedThisMonth: 5,
    availableLicenses: 5,
    reportedSold: 3,
    invoiceQuantity: 3,
    carryForward: 2,
  },
  {
    month: "August 2025",
    broughtForward: 2,
    issuedThisMonth: 6,
    availableLicenses: 8,
    reportedSold: 5,
    invoiceQuantity: 5,
    carryForward: 3,
  },
  {
    month: "September 2025",
    broughtForward: 3,
    issuedThisMonth: 7,
    availableLicenses: 10,
    reportedSold: 6,
    invoiceQuantity: 6,
    carryForward: 4,
  },
  {
    month: "October 2025",
    broughtForward: 4,
    issuedThisMonth: 7,
    availableLicenses: 11,
    reportedSold: 8,
    invoiceQuantity: 8,
    carryForward: 3,
  },
  {
    month: "November 2025",
    broughtForward: 3,
    issuedThisMonth: 8,
    availableLicenses: 11,
    reportedSold: 7,
    invoiceQuantity: 7,
    carryForward: 4,
  },
  {
    month: "December 2025",
    broughtForward: 4,
    issuedThisMonth: 6,
    availableLicenses: 10,
    reportedSold: 5,
    invoiceQuantity: 5,
    carryForward: 5,
  },
  {
    month: "January 2026",
    broughtForward: 5,
    issuedThisMonth: 6,
    availableLicenses: 11,
    reportedSold: 8,
    invoiceQuantity: 8,
    carryForward: 3,
  },
  {
    month: "February 2026",
    broughtForward: 3,
    issuedThisMonth: 8,
    availableLicenses: 11,
    reportedSold: 7,
    invoiceQuantity: 7,
    carryForward: 4,
  },
  {
    month: "March 2026",
    broughtForward: 4,
    issuedThisMonth: 6,
    availableLicenses: 10,
    reportedSold: 6,
    invoiceQuantity: 6,
    carryForward: 4,
  },
  {
    month: "April 2026",
    broughtForward: 4,
    issuedThisMonth: 8,
    availableLicenses: 12,
    reportedSold: 8,
    invoiceQuantity: 8,
    carryForward: 4,
  },
  {
    month: "May 2026",
    broughtForward: 4,
    issuedThisMonth: 9,
    availableLicenses: 13,
    reportedSold: 9,
    invoiceQuantity: 9,
    carryForward: 4,
  },
];

export const mockLicenses: LicenseRecord[] = [
  {
    key: "OCUMAPS-100-OCU-001",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Activated",
    issuedDate: "2026-06-02",
    defaultSold: true,
    laasVerification: "Verified active",
  },
  {
    key: "OCUMAPS-100-OCU-002",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Activated",
    issuedDate: "2026-06-02",
    defaultSold: true,
    laasVerification: "Verified active",
  },
  {
    key: "OCUMAPS-100-OCU-003",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Activated",
    issuedDate: "2026-06-02",
    defaultSold: true,
    laasVerification: "Verified active",
  },
  {
    key: "OCUMAPS-100-OCU-004",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Activated",
    issuedDate: "2026-06-02",
    defaultSold: true,
    laasVerification: "Verified active",
  },
  {
    key: "OCUMAPS-100-OCU-005",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Not activated",
    issuedDate: "2026-06-02",
    defaultSold: true,
    laasVerification: "Needs review",
  },
  {
    key: "OCUMAPS-100-OCU-006",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Not activated",
    issuedDate: "2026-06-02",
    defaultSold: true,
    laasVerification: "Needs review",
  },
  {
    key: "OCUMAPS-100-OCU-007",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Not activated",
    issuedDate: "2026-06-02",
    defaultSold: false,
    laasVerification: "Not checked",
  },
  {
    key: "OCUMAPS-100-OCU-008",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Not activated",
    issuedDate: "2026-06-02",
    defaultSold: false,
    laasVerification: "Not checked",
  },
  {
    key: "OCUMAPS-100-OCU-009",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Not activated",
    issuedDate: "2026-06-02",
    defaultSold: false,
    laasVerification: "Not checked",
  },
  {
    key: "OCUMAPS-100-OCU-010",
    product: mockProduct,
    productVersion: mockProductVersion,
    client: mockClient,
    country: mockClientCountry,
    activationStatus: "Not activated",
    issuedDate: "2026-06-02",
    defaultSold: false,
    laasVerification: "Not checked",
  },
];
