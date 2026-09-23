import './Pagination.css';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ currentPage, totalPages, totalItems, pageSize, onPageChange }: PaginationProps) {
  const start = (currentPage - 1) * pageSize + 1;
  const end = Math.min(currentPage * pageSize, totalItems);

  const pages: (number | '...')[] = [];
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || Math.abs(i - currentPage) <= 1) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...');
    }
  }

  return (
    <div className="pagination">
      <button className="pagination__btn" disabled={currentPage <= 1} onClick={() => onPageChange(currentPage - 1)}>← PREV</button>
      {pages.map((p, i) => (
        p === '...' ? (
          <span key={`e${i}`} style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>…</span>
        ) : (
          <button
            key={p}
            className={`pagination__btn ${p === currentPage ? 'pagination__btn--active' : ''}`}
            onClick={() => onPageChange(p)}
          >{p}</button>
        )
      ))}
      <button className="pagination__btn" disabled={currentPage >= totalPages} onClick={() => onPageChange(currentPage + 1)}>NEXT →</button>
      <span className="pagination__info">Showing {start}–{end} of {totalItems} alerts</span>
    </div>
  );
}
