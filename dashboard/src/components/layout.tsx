import { Link } from 'react-router-dom';
import { Swords } from 'lucide-react';

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <nav className="border-b border-white/5 bg-black/30 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors">
            <Swords className="w-5 h-5" />
            <span className="font-bold tracking-wider text-sm uppercase">LoL Stats</span>
          </Link>
          <Link
            to="/compare"
            className="ml-auto text-sm text-white/50 hover:text-white/80 transition-colors"
          >
            Compare Players
          </Link>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  );
}
