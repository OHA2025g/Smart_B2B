import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export function AppShell({ sidebar }) {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 overflow-x-hidden">
      <Navbar />
      <div className="flex flex-1 overflow-x-hidden">
        {sidebar && <aside className="hidden lg:block w-56 shrink-0 border-r border-neutral-200 bg-white">{sidebar}</aside>}
        <main className="flex-1 min-w-0 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
