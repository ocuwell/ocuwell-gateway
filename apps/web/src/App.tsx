import {
  ArrowRight,
  Building2,
  CheckCircle2,
  ClipboardList,
  CreditCard,
  Eye,
  FileText,
  KeyRound,
  MapPin,
  PackagePlus,
  Receipt,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  ShoppingCart,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  DashboardCard,
  InvoiceInbox,
  LicenseTable,
  MonthlyBalanceChart,
  RequestCardList,
  RequestTable,
  StatusBadge,
} from "./components";
import {
  buildInvoice,
  buildMonthlyReport,
  mockClient,
  mockClientCountry,
  mockLicenses,
  mockMonth,
  mockMonthlyHistory,
  mockProduct,
  mockProductVersion,
  mockRequests,
} from "./mockData";
import type { InvoiceStatus } from "./mockData";

type PortalMode = "admin" | "client";

export function App() {
  const [mode, setMode] = useState<PortalMode>(readInitialMode());
  const [toast, setToast] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [productFilter, setProductFilter] = useState("All products");
  const [monthFilter, setMonthFilter] = useState(mockMonth);
  const [invoiceStatusFilter, setInvoiceStatusFilter] = useState("All statuses");
  const [invoiceReference, setInvoiceReference] = useState("Pending");
  const [invoiceStatus, setInvoiceStatus] = useState<InvoiceStatus>("Draft");
  const [soldKeys, setSoldKeys] = useState<Set<string>>(
    () => new Set(mockLicenses.filter((license) => license.defaultSold).map((license) => license.key)),
  );

  const monthlyReport = useMemo(() => buildMonthlyReport(soldKeys.size), [soldKeys]);
  const invoice = useMemo(
    () => buildInvoice(monthlyReport.invoiceQuantity, invoiceStatus, invoiceReference),
    [invoiceReference, invoiceStatus, monthlyReport.invoiceQuantity],
  );

  // No LicenseSpring/LAAS API key should ever be exposed in this frontend.
  // TODO: replace mock data with backend API through a secured server gateway.
  function switchMode(nextMode: PortalMode) {
    setMode(nextMode);
    window.history.replaceState(null, "", nextMode === "admin" ? "/admin-portal" : "/client-portal");
  }

  function showPrototypeToast(message = "Prototype only. No real data was changed.") {
    setToast(message);
    window.setTimeout(() => setToast(""), 2600);
  }

  function toggleLicenseSold(licenseKey: string, sold: boolean) {
    setSoldKeys((currentKeys) => {
      const nextKeys = new Set(currentKeys);
      if (sold) {
        nextKeys.add(licenseKey);
      } else {
        nextKeys.delete(licenseKey);
      }
      return nextKeys;
    });
    showPrototypeToast(sold ? "Marked as sold for the monthly report." : "Removed from sold report.");
  }

  function ensureInvoiceReference() {
    const generatedReference = `INV-OCU-2026-${String(monthlyReport.invoiceQuantity).padStart(4, "0")}`;
    setInvoiceReference((currentReference) =>
      currentReference === "Pending" ? generatedReference : currentReference,
    );
    return generatedReference;
  }

  function generateInvoice() {
    ensureInvoiceReference();
    setInvoiceStatus("Draft");
    showPrototypeToast("Prototype invoice generated from the sold-license count.");
  }

  function sendInvoice() {
    ensureInvoiceReference();
    setInvoiceStatus("Payment Pending");
    showPrototypeToast("Prototype invoice sent to OCULUS invoice inbox.");
  }

  function clientSubmitPayment() {
    if (invoiceStatus !== "Payment Pending") {
      showPrototypeToast("Prototype only: invoice must be sent before payment can be submitted.");
      return;
    }
    setInvoiceStatus("Payment Submitted");
    showPrototypeToast("Payment submitted for admin review.");
  }

  function reviewPayment() {
    if (invoiceStatus !== "Payment Submitted") {
      showPrototypeToast("Prototype only: no submitted payment is waiting for review.");
      return;
    }
    setInvoiceStatus("Under Review");
    showPrototypeToast("Payment moved to admin review.");
  }

  function approvePayment() {
    if (invoiceStatus !== "Under Review" && invoiceStatus !== "Payment Submitted") {
      showPrototypeToast("Prototype only: payment is not ready for approval.");
      return;
    }
    setInvoiceStatus("Payment Complete");
    showPrototypeToast("Payment approved. Client invoice now shows payment complete.");
  }

  return (
    <main className="hub-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            O
          </span>
          <div>
            <p>Licensing Management Hub MVP</p>
            <span>OCULUS distributor prototype for OCUMAPS v1.0.0</span>
          </div>
        </div>

        <div className="portal-switch" aria-label="Portal view">
          <button
            className={mode === "admin" ? "active" : ""}
            type="button"
            onClick={() => switchMode("admin")}
          >
            <ShieldCheck size={17} aria-hidden="true" />
            Admin
          </button>
          <button
            className={mode === "client" ? "active" : ""}
            type="button"
            onClick={() => switchMode("client")}
          >
            <Building2 size={17} aria-hidden="true" />
            Client
          </button>
        </div>
      </header>

      <SearchToolbar
        invoiceStatusFilter={invoiceStatusFilter}
        monthFilter={monthFilter}
        productFilter={productFilter}
        searchTerm={searchTerm}
        setInvoiceStatusFilter={setInvoiceStatusFilter}
        setMonthFilter={setMonthFilter}
        setProductFilter={setProductFilter}
        setSearchTerm={setSearchTerm}
      />

      <ContextStrip />

      {mode === "admin" ? (
        <AdminDashboard
          invoice={invoice}
          monthlyReport={monthlyReport}
          soldKeys={soldKeys}
          onApprovePayment={approvePayment}
          onGenerateInvoice={generateInvoice}
          onPrototypeAction={showPrototypeToast}
          onReviewPayment={reviewPayment}
          onSendInvoice={sendInvoice}
        />
      ) : (
        <ClientDashboard
          invoice={invoice}
          monthlyReport={monthlyReport}
          soldKeys={soldKeys}
          onPrototypeAction={showPrototypeToast}
          onSubmitPayment={clientSubmitPayment}
          onToggleSold={toggleLicenseSold}
        />
      )}

      {toast ? <div className="toast">{toast}</div> : null}
    </main>
  );
}

function AdminDashboard({
  invoice,
  monthlyReport,
  onApprovePayment,
  onGenerateInvoice,
  onPrototypeAction,
  onReviewPayment,
  onSendInvoice,
  soldKeys,
}: {
  invoice: ReturnType<typeof buildInvoice>;
  monthlyReport: ReturnType<typeof buildMonthlyReport>;
  onApprovePayment: () => void;
  onGenerateInvoice: () => void;
  onPrototypeAction: (message?: string) => void;
  onReviewPayment: () => void;
  onSendInvoice: () => void;
  soldKeys: ReadonlySet<string>;
}) {
  const [soldReportSearch, setSoldReportSearch] = useState("");
  const [soldReportFilter, setSoldReportFilter] = useState("All licenses");
  const laasReviewCount = mockLicenses.filter(
    (license) => soldKeys.has(license.key) && license.laasVerification === "Needs review",
  ).length;
  const filteredSoldReportLicenses = mockLicenses.filter((license) => {
    const searchValue = soldReportSearch.trim().toLowerCase();
    const matchesSearch =
      !searchValue ||
      license.key.toLowerCase().includes(searchValue) ||
      license.product.toLowerCase().includes(searchValue) ||
      license.activationStatus.toLowerCase().includes(searchValue) ||
      license.laasVerification.toLowerCase().includes(searchValue);
    const isSold = soldKeys.has(license.key);
    const matchesFilter =
      soldReportFilter === "All licenses" ||
      (soldReportFilter === "Sold by OCULUS" && isSold) ||
      (soldReportFilter === "Carry forward" && !isSold) ||
      (soldReportFilter === "Needs LAAS review" && license.laasVerification === "Needs review") ||
      (soldReportFilter === "Verified active" && license.laasVerification === "Verified active");

    return matchesSearch && matchesFilter;
  });

  // TODO: add auth guard for admin role before rendering this portal.
  return (
    <>
      <PageHeader
        badge="Prototype / Demo Data"
        icon={<ShieldCheck size={22} aria-hidden="true" />}
        subtitle="OCULUS Distributor Overview"
        title="Admin Licensing Dashboard"
      />

      <WorkflowStrip monthlyReport={monthlyReport} />

      <section className="kpi-grid" aria-label="Admin summary">
        <DashboardCard
          helper="Brought forward plus issued this month"
          icon={<KeyRound size={21} />}
          label="Available Licenses"
          tone="primary"
          value={monthlyReport.availableLicenses}
        />
        <DashboardCard
          helper="Marked sold by OCULUS"
          icon={<ShoppingCart size={21} />}
          label="Sold This Month"
          value={monthlyReport.reportedSold}
        />
        <DashboardCard
          helper="Generated from sold count"
          icon={<Receipt size={21} />}
          label="Invoice Quantity"
          value={monthlyReport.invoiceQuantity}
        />
        <DashboardCard
          helper="Current invoice lifecycle"
          icon={<CreditCard size={21} />}
          label="Invoice Status"
          value={invoice.status}
        />
      </section>

      <section className="content-grid admin-content-grid">
        <Panel className="queue-panel" eyebrow="Admin queue" title="Operational checks">
          <div className="admin-queue">
            <QueueItem
              detail="1 request"
              label="Pending request"
              status="Pending"
            />
            <QueueItem
              detail={`${monthlyReport.reportedSold} sold`}
              label="Monthly report"
              status={monthlyReport.reportStatus}
            />
            <QueueItem
              detail={`${laasReviewCount} check`}
              label="LAAS review"
              status={laasReviewCount > 0 ? "Needs review" : "Verified active"}
            />
            <QueueItem
              detail={invoice.reference}
              label="Invoice"
              status={invoice.status}
            />
          </div>
          <BalanceBadge monthlyReport={monthlyReport} />
          <div className="action-grid compact-actions">
            <PrototypeAction icon={<PackagePlus size={17} />} label="Issue Licenses" onClick={onPrototypeAction} />
            <PrototypeAction icon={<CheckCircle2 size={17} />} label="Approve Report" onClick={onPrototypeAction} />
            <PrototypeAction
              icon={<RefreshCw size={17} />}
              label="Verify with LAAS"
              onClick={() => {
                // TODO: connect license status verification to LicenseSpring/LAAS through backend only.
                onPrototypeAction("Prototype only: backend LAAS verification would run here.");
              }}
            />
          </div>
        </Panel>

        <Panel className="chart-panel" eyebrow="Monthly balance" title="Issued, sold, and carry-forward trend">
          <MonthlyBalanceChart currentReport={monthlyReport} history={mockMonthlyHistory} />
        </Panel>

        <Panel className="wide-panel" eyebrow="Invoice management" title="Invoice inbox and payment approval">
          <InvoiceInbox
            invoice={invoice}
            primaryAction={
              <button className="primary-button" type="button" onClick={onGenerateInvoice}>
                <Receipt size={16} aria-hidden="true" />
                Generate Invoice
              </button>
            }
            secondaryActions={
              <>
                <button className="secondary-button" type="button" onClick={() => onPrototypeAction("Prototype only: invoice preview opened.")}>
                  <Eye size={16} aria-hidden="true" />
                  View Invoice
                </button>
                <button className="secondary-button" type="button" onClick={onSendInvoice}>
                  <Send size={16} aria-hidden="true" />
                  Send Invoice
                </button>
                <button className="secondary-button" type="button" onClick={onReviewPayment}>
                  <ClipboardList size={16} aria-hidden="true" />
                  Review Payment
                </button>
                <button className="secondary-button" type="button" onClick={onApprovePayment}>
                  <CheckCircle2 size={16} aria-hidden="true" />
                  Approve Payment
                </button>
              </>
            }
          />
        </Panel>

        <Panel className="wide-panel" eyebrow="License requests" title="OCULUS request queue">
          <RequestTable requests={mockRequests} showAdminActions onAction={onPrototypeAction} />
        </Panel>

        <Panel className="wide-panel" eyebrow="Issued licenses" title="Sold report and LAAS verification view">
          <div className="sold-report-toolbar" aria-label="Sold report search and filters">
            <label className="sold-report-search">
              <Search size={17} aria-hidden="true" />
              <span>Search sold report</span>
              <input
                placeholder="License key, product, activation, LAAS status..."
                type="search"
                value={soldReportSearch}
                onChange={(event) => setSoldReportSearch(event.target.value)}
              />
            </label>
            <label>
              Filter
              <select value={soldReportFilter} onChange={(event) => setSoldReportFilter(event.target.value)}>
                <option>All licenses</option>
                <option>Sold by OCULUS</option>
                <option>Carry forward</option>
                <option>Needs LAAS review</option>
                <option>Verified active</option>
              </select>
            </label>
            <div className="sold-report-count">
              <span>Showing</span>
              <strong>{filteredSoldReportLicenses.length} licenses</strong>
            </div>
          </div>
          <LicenseTable
            licenses={filteredSoldReportLicenses}
            showClient
            showLaas
            showSoldAssigned
            soldKeys={soldKeys}
          />
        </Panel>
      </section>
    </>
  );
}

function ClientDashboard({
  invoice,
  monthlyReport,
  onPrototypeAction,
  onSubmitPayment,
  onToggleSold,
  soldKeys,
}: {
  invoice: ReturnType<typeof buildInvoice>;
  monthlyReport: ReturnType<typeof buildMonthlyReport>;
  onPrototypeAction: (message?: string) => void;
  onSubmitPayment: () => void;
  onToggleSold: (licenseKey: string, sold: boolean) => void;
  soldKeys: ReadonlySet<string>;
}) {
  const [requestQuantity, setRequestQuantity] = useState(10);
  const [requestNotes, setRequestNotes] = useState("Additional OCUMAPS licenses for July onboarding.");
  const [reportNotes, setReportNotes] = useState("June sales report submitted for invoicing.");

  // TODO: add auth guard for client distributor role.
  // TODO: enforce that client users can only see their own distributor data.
  return (
    <>
      <PageHeader
        badge="Prototype / Demo Data"
        icon={<Building2 size={22} aria-hidden="true" />}
        subtitle="License stock, sold reporting, and invoice status"
        title="OCULUS Distributor Portal"
      />

      <WorkflowStrip monthlyReport={monthlyReport} />

      <section className="kpi-grid" aria-label="Client summary">
        <DashboardCard
          helper="Stock available this month"
          icon={<KeyRound size={21} />}
          label="Available Licenses"
          tone="primary"
          value={monthlyReport.availableLicenses}
        />
        <DashboardCard
          helper="Ticked in the license list"
          icon={<ShoppingCart size={21} />}
          label="Reported Sold"
          value={monthlyReport.reportedSold}
        />
        <DashboardCard
          helper="Based on sold licenses"
          icon={<Receipt size={21} />}
          label="Invoice Quantity"
          value={monthlyReport.invoiceQuantity}
        />
        <DashboardCard
          helper="Unused licenses for next month"
          icon={<RefreshCw size={21} />}
          label="Carry Forward"
          value={monthlyReport.carryForward}
        />
      </section>

      <section className="content-grid">
        <Panel eyebrow="Request licenses" title="Request more OCUMAPS stock">
          <div className="request-form-grid">
            <label>
              Quantity
              <input
                min={1}
                type="number"
                value={requestQuantity}
                onChange={(event) => setRequestQuantity(Number(event.target.value) || 1)}
              />
            </label>
            <label>
              Notes
              <textarea value={requestNotes} onChange={(event) => setRequestNotes(event.target.value)} />
            </label>
          </div>
          <button
            className="primary-button full-width"
            type="button"
            onClick={() => onPrototypeAction(`Prototype only: request for ${requestQuantity} OCUMAPS licenses.`)}
          >
            <ShoppingCart size={16} aria-hidden="true" />
            Request More Licenses
          </button>
          <RequestCardList requests={mockRequests} onAction={onPrototypeAction} />
        </Panel>

        <Panel className="chart-panel" eyebrow="Monthly balance" title="Issued, sold, and carry-forward trend">
          <MonthlyBalanceChart currentReport={monthlyReport} history={mockMonthlyHistory} />
        </Panel>

        <Panel className="wide-panel reporting-panel" eyebrow="Monthly report" title="Tick sold licenses, then submit report">
          <div className="reporting-summary">
            <div>
              <span>Report Status</span>
              <StatusBadge label={monthlyReport.reportStatus} />
            </div>
            <div>
              <span>Sold Selected</span>
              <strong>{monthlyReport.reportedSold}</strong>
            </div>
            <div>
              <span>Invoice Quantity</span>
              <strong>{monthlyReport.invoiceQuantity}</strong>
            </div>
            <div>
              <span>Carry Forward</span>
              <strong>{monthlyReport.carryForward}</strong>
            </div>
          </div>
          <LicenseTable
            canToggleSold
            licenses={mockLicenses}
            onToggleSold={onToggleSold}
            soldKeys={soldKeys}
          />
          <div className="report-submit-row">
            <label className="notes-field">
              Notes
              <textarea value={reportNotes} onChange={(event) => setReportNotes(event.target.value)} />
            </label>
            <div className="report-submit-action">
              <span>{monthlyReport.reportedSold} sold licenses selected</span>
              <button className="primary-button report-submit-button" type="button" onClick={() => onPrototypeAction()}>
                <ClipboardList size={16} aria-hidden="true" />
                Submit Monthly Report
              </button>
            </div>
          </div>
        </Panel>

        <Panel className="wide-panel client-invoice-panel" eyebrow="Invoice inbox" title="Manage invoices from admin">
          <ClientInvoiceInbox
            invoice={invoice}
            onPrototypeAction={onPrototypeAction}
            onSubmitPayment={onSubmitPayment}
          />
        </Panel>
      </section>
    </>
  );
}

function ClientInvoiceInbox({
  invoice,
  onPrototypeAction,
  onSubmitPayment,
}: {
  invoice: ReturnType<typeof buildInvoice>;
  onPrototypeAction: (message?: string) => void;
  onSubmitPayment: () => void;
}) {
  const steps = ["Payment Pending", "Payment Submitted", "Under Review", "Payment Complete"];
  const activeIndex = Math.max(steps.indexOf(invoice.status), 0);

  return (
    <article className="client-invoice-card">
      <div className="client-invoice-main">
        <div className="invoice-title-row">
          <div>
            <span>Current month invoice</span>
            <strong>{invoice.reference}</strong>
          </div>
          <StatusBadge label={invoice.status} />
        </div>
        <div className="client-invoice-grid">
          <div>
            <span>Month</span>
            <strong>{invoice.month}</strong>
          </div>
          <div>
            <span>Product</span>
            <strong>
              {invoice.product} v{invoice.productVersion}
            </strong>
          </div>
          <div>
            <span>Quantity billed</span>
            <strong>{invoice.quantity}</strong>
          </div>
          <div>
            <span>Demo amount</span>
            <strong>{formatCurrency(invoice.totalAmount)}</strong>
          </div>
        </div>
      </div>

      <div className="client-invoice-side">
        <div className="invoice-timeline" aria-label="Invoice payment status">
          {steps.map((step, index) => (
            <div className={`timeline-step ${index <= activeIndex ? "active" : ""}`} key={step}>
              <span />
              <strong>{step}</strong>
            </div>
          ))}
        </div>
        <div className="invoice-client-actions">
          <button className="primary-button" type="button" onClick={onSubmitPayment}>
            <CreditCard size={16} aria-hidden="true" />
            Mark Payment Submitted
          </button>
          <button className="secondary-button" type="button" onClick={() => onPrototypeAction("Prototype only: invoice preview opened.")}>
            <Eye size={16} aria-hidden="true" />
            View Invoice
          </button>
          <button className="secondary-button" type="button" onClick={() => onPrototypeAction("Prototype only: invoice download.")}>
            <FileText size={16} aria-hidden="true" />
            Download
          </button>
        </div>
      </div>
    </article>
  );
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-GB", {
    currency: "EUR",
    maximumFractionDigits: 0,
    style: "currency",
  }).format(value);
}

function SearchToolbar({
  invoiceStatusFilter,
  monthFilter,
  productFilter,
  searchTerm,
  setInvoiceStatusFilter,
  setMonthFilter,
  setProductFilter,
  setSearchTerm,
}: {
  invoiceStatusFilter: string;
  monthFilter: string;
  productFilter: string;
  searchTerm: string;
  setInvoiceStatusFilter: (value: string) => void;
  setMonthFilter: (value: string) => void;
  setProductFilter: (value: string) => void;
  setSearchTerm: (value: string) => void;
}) {
  return (
    <section className="search-toolbar" aria-label="Future search and filters">
      <label className="search-field">
        <Search size={17} aria-hidden="true" />
        <span>Search client</span>
        <input
          placeholder="OCULUS, future distributor, invoice..."
          type="search"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
        />
      </label>
      <label>
        Product
        <select value={productFilter} onChange={(event) => setProductFilter(event.target.value)}>
          <option>All products</option>
          <option>OCUMAPS v1.0.0</option>
        </select>
      </label>
      <label>
        Month
        <select value={monthFilter} onChange={(event) => setMonthFilter(event.target.value)}>
          <option>June 2026</option>
          <option>May 2026</option>
          <option>April 2026</option>
          <option>March 2026</option>
        </select>
      </label>
      <label>
        Invoice status
        <select value={invoiceStatusFilter} onChange={(event) => setInvoiceStatusFilter(event.target.value)}>
          <option>All statuses</option>
          <option>Draft</option>
          <option>Payment Pending</option>
          <option>Payment Submitted</option>
          <option>Under Review</option>
          <option>Payment Complete</option>
        </select>
      </label>
    </section>
  );
}

function ContextStrip() {
  return (
    <section className="context-strip" aria-label="Demo context">
      <ContextItem icon={<Building2 size={17} />} label="Client" value={mockClient} />
      <ContextItem icon={<MapPin size={17} />} label="Country" value={mockClientCountry} />
      <ContextItem icon={<KeyRound size={17} />} label="Product" value={`${mockProduct} v${mockProductVersion}`} />
      <ContextItem icon={<FileText size={17} />} label="Month" value={mockMonth} />
      <ContextItem icon={<ShieldCheck size={17} />} label="Environment" value="Prototype / Demo Data" />
    </section>
  );
}

function ContextItem({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div>
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PageHeader({
  badge,
  icon,
  subtitle,
  title,
}: {
  badge: string;
  icon: ReactNode;
  subtitle: string;
  title: string;
}) {
  return (
    <section className="page-header">
      <div className="header-icon">{icon}</div>
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <span className="env-badge">{badge}</span>
    </section>
  );
}

function WorkflowStrip({ monthlyReport }: { monthlyReport: ReturnType<typeof buildMonthlyReport> }) {
  return (
    <section className="formula-strip" aria-label="Monthly license formula">
      <FormulaStep label="Brought Forward" value={monthlyReport.broughtForward} />
      <span className="formula-op">+</span>
      <FormulaStep label="Issued" value={monthlyReport.issuedThisMonth} />
      <span className="formula-op">=</span>
      <FormulaStep label="Available" value={monthlyReport.availableLicenses} />
      <span className="formula-op">Sold</span>
      <FormulaStep label="Invoice Qty" value={monthlyReport.invoiceQuantity} />
      <span className="formula-op">Carry</span>
      <FormulaStep label="Forward" value={monthlyReport.carryForward} />
    </section>
  );
}

function FormulaStep({ label, value }: { label: string; value: number }) {
  return (
    <div className="formula-step">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Panel({
  children,
  className = "",
  eyebrow,
  title,
}: {
  children: ReactNode;
  className?: string;
  eyebrow: string;
  title: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-header">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function QueueItem({
  detail,
  label,
  status,
}: {
  detail: string;
  label: string;
  status: string;
}) {
  return (
    <div className="queue-item">
      <div>
        <strong>{label}</strong>
        <span>{detail}</span>
      </div>
      <StatusBadge label={status} />
    </div>
  );
}

function BalanceBadge({ monthlyReport }: { monthlyReport: ReturnType<typeof buildMonthlyReport> }) {
  const soldPercent = Math.round(
    (monthlyReport.reportedSold / Math.max(monthlyReport.availableLicenses, 1)) * 100,
  );

  return (
    <section className="balance-badge" aria-label="Monthly balance summary">
      <div
        className="balance-pie"
        style={{
          background: `conic-gradient(var(--gold) 0 ${soldPercent}%, rgba(19, 116, 92, 0.72) ${soldPercent}% 100%)`,
        }}
      >
        <span>{soldPercent}%</span>
      </div>
      <div className="balance-badge-copy">
        <span>Monthly balance</span>
        <strong>
          {monthlyReport.reportedSold} sold / {monthlyReport.carryForward} carry forward
        </strong>
        <p>
          {monthlyReport.broughtForward} brought forward + {monthlyReport.issuedThisMonth} issued ={" "}
          {monthlyReport.availableLicenses} available.
        </p>
      </div>
    </section>
  );
}

function PrototypeAction({
  icon,
  label,
  onClick,
}: {
  icon: ReactNode;
  label: string;
  onClick: (message?: string) => void;
}) {
  return (
    <button className="action-button" type="button" onClick={() => onClick("Prototype only. This action is not wired yet.")}>
      {icon}
      <span>{label}</span>
      <ArrowRight size={15} aria-hidden="true" />
    </button>
  );
}

function readInitialMode(): PortalMode {
  return window.location.pathname.includes("client") ? "client" : "admin";
}
