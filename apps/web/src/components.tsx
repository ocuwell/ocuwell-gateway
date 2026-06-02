import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { Invoice, LicenseRecord, LicenseRequest, MonthlyHistoryItem, MonthlyReport } from "./mockData";

export function DashboardCard({
  helper,
  icon,
  label,
  tone = "default",
  value,
}: {
  helper?: string;
  icon?: ReactNode;
  label: string;
  tone?: "default" | "primary";
  value: string | number;
}) {
  return (
    <section className={`dashboard-card ${tone === "primary" ? "primary-card" : ""}`}>
      {icon ? <div className="card-icon">{icon}</div> : null}
      <span>{label}</span>
      <strong>{value}</strong>
      {helper ? <p>{helper}</p> : null}
    </section>
  );
}

export function StatusBadge({ label }: { label: string }) {
  return <span className={`status-badge ${normalizeStatus(label)}`}>{label}</span>;
}

export function MonthlyBalanceTable({ report }: { report: MonthlyReport }) {
  const rows = [
    ["Brought Forward", report.broughtForward],
    ["Issued This Month", report.issuedThisMonth],
    ["Available Licenses", report.availableLicenses],
    ["Reported Sold", report.reportedSold],
    ["Invoice Quantity", report.invoiceQuantity],
    ["Carry Forward", report.carryForward],
  ];

  return (
    <div className="table-wrap">
      <table className="balance-table">
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <th>{label}</th>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RequestTable({
  requests,
  showAdminActions,
  onAction,
}: {
  requests: LicenseRequest[];
  showAdminActions?: boolean;
  onAction?: (message: string) => void;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Request ID</th>
            <th>Client</th>
            <th>Country</th>
            <th>Product</th>
            <th>Quantity</th>
            <th>Date</th>
            <th>Status</th>
            {showAdminActions ? <th>Actions</th> : null}
          </tr>
        </thead>
        <tbody>
          {requests.map((request) => (
            <tr key={request.id}>
              <td>{request.id}</td>
              <td>{request.client}</td>
              <td>{request.country}</td>
              <td>
                {request.product} v{request.productVersion}
              </td>
              <td>{request.quantity}</td>
              <td>{request.date}</td>
              <td>
                <StatusBadge label={request.status} />
              </td>
              {showAdminActions ? (
                <td>
                  <div className="inline-actions">
                    <button type="button" onClick={() => onAction?.("Prototype only: approval workflow.")}>
                      Approve
                    </button>
                    <button type="button" onClick={() => onAction?.("Prototype only: rejection workflow.")}>
                      Reject
                    </button>
                    <button type="button" onClick={() => onAction?.("Prototype only: license generation.")}>
                      Generate
                    </button>
                  </div>
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RequestCardList({
  requests,
  onAction,
}: {
  requests: LicenseRequest[];
  onAction?: (message: string) => void;
}) {
  return (
    <div className="request-card-list">
      {requests.map((request) => (
        <article className="request-card" key={request.id}>
          <div>
            <span>Request</span>
            <strong>{request.id}</strong>
          </div>
          <div>
            <span>Quantity</span>
            <strong>{request.quantity}</strong>
          </div>
          <div>
            <span>Product</span>
            <strong>
              {request.product} v{request.productVersion}
            </strong>
          </div>
          <div>
            <span>Date</span>
            <strong>{request.date}</strong>
          </div>
          <div className="request-card-footer">
            <StatusBadge label={request.status} />
            <button type="button" onClick={() => onAction?.("Prototype only: request detail view.")}>
              View
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}

export function MonthlyBalanceChart({
  currentReport,
  history,
}: {
  currentReport: MonthlyReport;
  history: MonthlyHistoryItem[];
}) {
  const items = useMemo<MonthlyHistoryItem[]>(
    () => [
      ...history,
      {
        month: currentReport.month,
        broughtForward: currentReport.broughtForward,
        issuedThisMonth: currentReport.issuedThisMonth,
        availableLicenses: currentReport.availableLicenses,
        reportedSold: currentReport.reportedSold,
        invoiceQuantity: currentReport.invoiceQuantity,
        carryForward: currentReport.carryForward,
      },
    ],
    [currentReport, history],
  );
  const [selectedMonth, setSelectedMonth] = useState(currentReport.month);
  const selectedItem = items.find((item) => item.month === selectedMonth) ?? items[items.length - 1];
  const chartWidth = 920;
  const chartHeight = 320;
  const margin = { bottom: 48, left: 44, right: 24, top: 28 };
  const plotWidth = chartWidth - margin.left - margin.right;
  const plotHeight = chartHeight - margin.top - margin.bottom;
  const maxValue = Math.max(...items.map((item) => item.availableLicenses), 1);
  const xForIndex = (index: number) =>
    margin.left + (items.length === 1 ? 0 : (index / (items.length - 1)) * plotWidth);
  const yForValue = (value: number) => margin.top + plotHeight - (value / maxValue) * plotHeight;
  const availablePoints = items.map((item, index) => `${xForIndex(index)},${yForValue(item.availableLicenses)}`).join(" ");
  const carryPoints = items.map((item, index) => `${xForIndex(index)},${yForValue(item.carryForward)}`).join(" ");
  const selectedIndex = Math.max(items.findIndex((item) => item.month === selectedItem.month), 0);
  const selectedX = xForIndex(selectedIndex);
  const barWidth = Math.max(12, Math.min(28, plotWidth / items.length - 14));

  return (
    <div className="balance-chart">
      <div className="chart-legend" aria-label="Chart legend">
        <span className="sold">Sold / invoice quantity</span>
        <span className="available">Available stock</span>
        <span className="carry">Carry forward</span>
      </div>

      <div className="balance-graph" aria-label="12 month license balance graph">
        <svg className="balance-svg" role="img" viewBox={`0 0 ${chartWidth} ${chartHeight}`}>
          <title>12 month OCUMAPS license balance</title>
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = margin.top + plotHeight - ratio * plotHeight;
            return (
              <g className="grid-line" key={ratio}>
                <line x1={margin.left} x2={chartWidth - margin.right} y1={y} y2={y} />
                <text x={12} y={y + 4}>{Math.round(maxValue * ratio)}</text>
              </g>
            );
          })}
          <line
            className="selected-month-line"
            x1={selectedX}
            x2={selectedX}
            y1={margin.top}
            y2={margin.top + plotHeight}
          />
          {items.map((item, index) => {
            const x = xForIndex(index);
            const y = yForValue(item.reportedSold);
            const height = margin.top + plotHeight - y;
            return (
              <rect
                className={`sold-bar ${item.month === selectedItem.month ? "active" : ""}`}
                height={height}
                key={item.month}
                rx={5}
                width={barWidth}
                x={x - barWidth / 2}
                y={y}
              />
            );
          })}
          <polyline className="available-line" points={availablePoints} />
          <polyline className="carry-line" points={carryPoints} />
          {items.map((item, index) => {
            const x = xForIndex(index);
            return (
              <g className="point-group" key={item.month}>
                <circle
                  className={`available-point ${item.month === selectedItem.month ? "active" : ""}`}
                  cx={x}
                  cy={yForValue(item.availableLicenses)}
                  r={item.month === selectedItem.month ? 5 : 3.6}
                />
                <circle
                  className={`carry-point ${item.month === selectedItem.month ? "active" : ""}`}
                  cx={x}
                  cy={yForValue(item.carryForward)}
                  r={item.month === selectedItem.month ? 5 : 3.6}
                />
                <text className="axis-label" textAnchor="middle" x={x} y={chartHeight - 16}>
                  {shortMonth(item.month)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="month-selector" aria-label="Select balance month">
        {items.map((item) => (
          <button
            className={`month-chip ${item.month === selectedItem.month ? "active" : ""}`}
            key={item.month}
            type="button"
            onClick={() => setSelectedMonth(item.month)}
          >
            <span>{shortMonth(item.month)}</span>
            <strong>{item.reportedSold}</strong>
          </button>
        ))}
      </div>

      <div className="chart-detail">
        <div>
          <span>Selected Month</span>
          <strong>{selectedItem.month}</strong>
        </div>
        <div>
          <span>Available</span>
          <strong>{selectedItem.availableLicenses}</strong>
        </div>
        <div>
          <span>Sold / Invoice Qty</span>
          <strong>{selectedItem.invoiceQuantity}</strong>
        </div>
        <div>
          <span>Carry Forward</span>
          <strong>{selectedItem.carryForward}</strong>
        </div>
      </div>
    </div>
  );
}

export function LicenseTable({
  canToggleSold,
  licenses,
  onToggleSold,
  showClient,
  showCountry,
  showLaas,
  showSoldAssigned,
  soldKeys,
}: {
  canToggleSold?: boolean;
  licenses: LicenseRecord[];
  onToggleSold?: (licenseKey: string, sold: boolean) => void;
  showClient?: boolean;
  showCountry?: boolean;
  showLaas?: boolean;
  showSoldAssigned?: boolean;
  soldKeys: ReadonlySet<string>;
}) {
  return (
    <div className="table-wrap license-table-wrap">
      <table>
        <thead>
          <tr>
            {canToggleSold ? <th>Sold</th> : null}
            <th>License Key / Reference</th>
            <th>Product</th>
            {showClient ? <th>Client</th> : null}
            {showCountry ? <th>Country</th> : null}
            <th>Sold Status</th>
            <th>Activation Status</th>
            <th>Issued Date</th>
            {showLaas ? <th>LAAS Check</th> : null}
            {showSoldAssigned ? <th>Admin Note</th> : null}
          </tr>
        </thead>
        <tbody>
          {licenses.map((license) => {
            const isSold = soldKeys.has(license.key);

            return (
              <tr key={license.key}>
                {canToggleSold ? (
                  <td>
                    <label className="sold-check">
                      <input
                        aria-label={`Mark ${license.key} as sold`}
                        checked={isSold}
                        type="checkbox"
                        onChange={(event) => onToggleSold?.(license.key, event.target.checked)}
                      />
                      <span>{isSold ? "Sold" : "Unsold"}</span>
                    </label>
                  </td>
                ) : null}
                <td>{license.key}</td>
                <td>
                  {license.product} v{license.productVersion}
                </td>
                {showClient ? <td>{license.client}</td> : null}
                {showCountry ? <td>{license.country}</td> : null}
                <td>
                  <StatusBadge label={isSold ? "Sold by OCULUS" : "Carry Forward"} />
                </td>
                <td>{license.activationStatus}</td>
                <td>{license.issuedDate}</td>
                {showLaas ? (
                  <td>
                    <StatusBadge label={license.laasVerification} />
                  </td>
                ) : null}
                {showSoldAssigned ? (
                  <td>{isSold ? "Included in invoice quantity" : "Unused stock rolls forward"}</td>
                ) : null}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function InvoiceSummary({
  invoice,
  message,
  onAddReference,
}: {
  invoice: Invoice;
  message?: string;
  onAddReference?: () => void;
}) {
  return (
    <div className="invoice-summary">
      <div>
        <span>Invoice Reference</span>
        <strong>{invoice.reference}</strong>
      </div>
      <div>
        <span>Month</span>
        <strong>{invoice.month}</strong>
      </div>
      <div>
        <span>Invoice Quantity</span>
        <strong>{invoice.quantity}</strong>
      </div>
      <div>
        <span>Demo Total</span>
        <strong>{formatCurrency(invoice.totalAmount)}</strong>
      </div>
      <div>
        <span>Invoice Status</span>
        <StatusBadge label={invoice.status} />
      </div>
      {message ? <p>{message}</p> : null}
      {onAddReference ? (
        <button className="secondary-button" type="button" onClick={onAddReference}>
          Add Invoice Reference
        </button>
      ) : null}
    </div>
  );
}

export function InvoiceInbox({
  invoice,
  primaryAction,
  secondaryActions,
}: {
  invoice: Invoice;
  primaryAction?: ReactNode;
  secondaryActions?: ReactNode;
}) {
  return (
    <article className="invoice-inbox-card">
      <div className="invoice-inbox-header">
        <div>
          <span>Invoice</span>
          <strong>{invoice.reference}</strong>
        </div>
        <StatusBadge label={invoice.status} />
      </div>
      <div className="invoice-inbox-grid">
        <div>
          <span>Client</span>
          <strong>{invoice.client}, {invoice.country}</strong>
        </div>
        <div>
          <span>Product</span>
          <strong>
            {invoice.product} v{invoice.productVersion}
          </strong>
        </div>
        <div>
          <span>Month</span>
          <strong>{invoice.month}</strong>
        </div>
        <div>
          <span>Sold / Invoice Qty</span>
          <strong>{invoice.quantity}</strong>
        </div>
        <div>
          <span>Demo Amount</span>
          <strong>{formatCurrency(invoice.totalAmount)}</strong>
        </div>
      </div>
      <div className="invoice-inbox-actions">
        {primaryAction}
        {secondaryActions}
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

function shortMonth(month: string) {
  return month.replace(" 2025", "").replace(" 2026", "").slice(0, 3);
}

function normalizeStatus(status: string) {
  return status.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
