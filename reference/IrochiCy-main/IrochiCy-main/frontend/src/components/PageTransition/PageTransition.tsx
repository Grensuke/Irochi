import { useLocation } from 'react-router-dom';
import './PageTransition.css';

interface PageTransitionProps {
  children: React.ReactNode;
}

export default function PageTransition({ children }: PageTransitionProps) {
  const location = useLocation();
  return (
    <div className="page-transition" key={location.pathname}>
      {children}
    </div>
  );
}
