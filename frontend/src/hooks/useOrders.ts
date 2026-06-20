import { useState, useEffect } from 'react';
import orderApi, { Order } from '@/api/orderApi';

export function useOrders(filters?: { status?: string; customerId?: string }) {
  const [data, setData] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        const response = await orderApi.getAll(filters);
        setData(response.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch orders');
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [filters]);

  return { data, loading, error };
}

export default useOrders;
