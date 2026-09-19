interface Column<T> {
  header: string;
  accessor: (row: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  isLoading?: boolean;
  emptyState?: React.ReactNode;
}

export function Table<T>({ columns, data, keyExtractor, isLoading, emptyState }: TableProps<T>) {
  if (!isLoading && data.length === 0 && emptyState) {
    return <>{emptyState}</>;
  }

  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface">
            {columns.map((col) => (
              <th key={col.header} className="px-4 py-3 text-left font-medium text-text-muted">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading
            ? Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-border last:border-0">
                  {columns.map((col) => (
                    <td key={col.header} className="px-4 py-3">
                      <div className="h-4 w-24 animate-pulse rounded-sm bg-border/60" />
                    </td>
                  ))}
                </tr>
              ))
            : data.map((row) => (
                <tr
                  key={keyExtractor(row)}
                  className="border-b border-border last:border-0 transition-colors hover:bg-surface/60"
                >
                  {columns.map((col) => (
                    <td key={col.header} className={`px-4 py-3 text-text ${col.className ?? ""}`}>
                      {col.accessor(row)}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  );
}