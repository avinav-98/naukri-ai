function renderCell(row, column) {
  const value = row[column.key];
  if (column.type === "link") {
    if (!value) {
      return "-";
    }
    return (
      <a href={value} rel="noreferrer" target="_blank">
        Open
      </a>
    );
  }
  if (column.type === "list") {
    return Array.isArray(value) && value.length ? value.join(", ") : "-";
  }
  return value || "-";
}

export function DataTable({ columns, rows }) {
  return (
    <div className="table-shell">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, index) => (
              <tr key={row.id || row.url || row.job_url || `${row.title || "row"}-${index}`}>
                {columns.map((column) => (
                  <td key={column.key}>{renderCell(row, column)}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>No records available.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
