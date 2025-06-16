'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle } from 'lucide-react';

export function DataConfirmationTab() {
  return (
    <div className="h-full overflow-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 页面标题 */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Step 2: Data Confirmation</h1>
          <p className="text-muted-foreground mt-2">
            Review and confirm the scraped data before proceeding to analysis.
          </p>
        </div>

        {/* 占位符内容 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Data Confirmation
              <Badge variant="secondary">Coming Soon</Badge>
            </CardTitle>
            <CardDescription>
              This step will allow you to review and validate the scraped product and review data.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-muted-foreground">
              <div className="text-lg font-medium mb-2">Step 2 Implementation</div>
              <p>This tab will display:</p>
              <ul className="list-disc list-inside mt-4 space-y-1 text-left max-w-md mx-auto">
                <li>Summary of scraped products and reviews</li>
                <li>Data quality validation</li>
                <li>Preview of product information</li>
                <li>Option to filter or exclude certain data</li>
                <li>Confirmation to proceed to analysis</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 