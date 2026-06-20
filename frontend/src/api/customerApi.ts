import apiClient from './client';

export interface Customer {
  id: string;
  code: string;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateCustomerDto {
  code: string;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
}

export interface UpdateCustomerDto {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  isActive?: boolean;
}

export const customerApi = {
  getAll: () => apiClient.get<Customer[]>('/customers'),
  getById: (id: string) => apiClient.get<Customer>(`/customers/${id}`),
  create: (data: CreateCustomerDto) => apiClient.post<Customer>('/customers', data),
  update: (id: string, data: UpdateCustomerDto) => apiClient.patch<Customer>(`/customers/${id}`, data),
  delete: (id: string) => apiClient.delete(`/customers/${id}`),
};

export default customerApi;
