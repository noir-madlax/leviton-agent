import { ChartProvider } from '@/contexts/chart-context';
import { MainLayout } from '@/components/layout/main-layout';

export default function Home() {
  return (
    <ChartProvider>
      <MainLayout />
    </ChartProvider>
  );
}
