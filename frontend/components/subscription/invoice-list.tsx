import { Download, ExternalLink } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { Invoice } from '@/types/subscription';

interface InvoiceListProps {
  invoices: Invoice[];
}

export function InvoiceList({ invoices }: InvoiceListProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'paid':
        return <Badge className="bg-green-500">已支付</Badge>;
      case 'open':
        return <Badge variant="secondary">待支付</Badge>;
      case 'draft':
        return <Badge variant="outline">草稿</Badge>;
      case 'uncollectible':
        return <Badge variant="destructive">无法收款</Badge>;
      case 'void':
        return <Badge variant="secondary">已作废</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  if (invoices.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        暂无发票记录
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>日期</TableHead>
          <TableHead>描述</TableHead>
          <TableHead>金额</TableHead>
          <TableHead>状态</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map((invoice) => (
          <TableRow key={invoice.id}>
            <TableCell>{formatDate(invoice.created_at)}</TableCell>
            <TableCell>{invoice.description || '-'}</TableCell>
            <TableCell>
              {formatAmount(invoice.amount_due, invoice.currency)}
            </TableCell>
            <TableCell>{getStatusBadge(invoice.status)}</TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-2">
                {invoice.hosted_invoice_url && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(invoice.hosted_invoice_url, '_blank')}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                )}
                {invoice.pdf_url && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(invoice.pdf_url, '_blank')}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
