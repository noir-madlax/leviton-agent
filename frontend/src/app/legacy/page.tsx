import { ChartProvider } from '@/contexts/chart-context';
import { MainLayout } from '@/components/layout/main-layout';

export default function LegacyPage() {
  return (
    <ChartProvider>
      <MainLayout />
    </ChartProvider>
  );
} 