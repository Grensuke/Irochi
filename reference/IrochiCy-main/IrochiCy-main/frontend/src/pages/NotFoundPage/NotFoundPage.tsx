import { Link } from 'react-router-dom';
import './NotFoundPage.css';

export default function NotFoundPage() {
  return (
    <div className="not-found">
      <div className="not-found__code">404</div>
      <div className="not-found__text">Route not found</div>
      <Link to="/dashboard" className="not-found__link">← Return to Dashboard</Link>
    </div>
  );
}
