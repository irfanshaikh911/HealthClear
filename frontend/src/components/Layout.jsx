import Navbar from './Navbar';
import { useLocation } from 'react-router-dom';

const Layout = ({ children }) => {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  return (
    <div className="page-wrapper">
      <Navbar />
      <main className={isLanding ? '' : 'container'}>
        {children}
      </main>
    </div>
  );
};

export default Layout;
