import apiClient from './client';

export interface Order {
  id: string;
  orderNumber: string;
  customerId: string;
  customerName?: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'SCHEDULED' | 'IN_PRODUCTION' | 'COMPLETED' | 'SHIPPED' | 'REJECTED' | 'CANCELLED';
  totalAmount: number;
  currency: string;
  requestedDate: string;
  promisedDate?: string;
  shippedDate?: string;
  items: OrderItem[];
  createdAt: string;
  updatedAt: string;
}

export interface OrderItem {
  id: string;
  orderId: string;
  productId: string;
  productName?: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

export interface CreateOrderDto {
  customerId: string;
  requestedDate: string;
  items: CreateOrderItemDto[];
}

export interface CreateOrderItemDto {
  productId: string;
  quantity: number;
  unitPrice: number;
}

export interface SubmitOrderDto {
  reason?: string;
}

export interface ApproveOrderDto {
  reason?: string;
}

export interface RejectOrderDto {
  reason: string;
}

export const orderApi = {
  getAll: (params?: { status?: string; customerId?: string }) => 
    apiClient.get<Order[]>('/orders', { params }),
  
  getById: (id: string) => apiClient.get<Order>(`/orders/${id}`),
  
  create: (data: CreateOrderDto) => apiClient.post<Order>('/orders', data),
  
  submit: (id: string, data?: SubmitOrderDto) => 
    apiClient.post<Order>(`/orders/${id}/submit`, data),
  
  approve: (id: string, data?: ApproveOrderDto) => 
    apiClient.post<Order>(`/orders/${id}/approve`, data),
  
  reject: (id: string, data: RejectOrderDto) => 
    apiClient.post<Order>(`/orders/${id}/reject`, data),
  
  cancel: (id: string, reason?: string) => 
    apiClient.post<Order>(`/orders/${id}/cancel`, { reason }),
};

export default orderApi;
