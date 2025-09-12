import { TopNavigation } from './TopNavigation';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <TopNavigation />
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}