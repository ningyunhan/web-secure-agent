import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 60000,
});

// 指纹识别
export const recognize = (banner: string) =>
  api.post('/recognize', { banner });

// 批量测试
export const runBatchTest = () =>
  api.get('/batch-test/run');

// 知识库管理
export const listKnowledge = (type?: string) =>
  api.get('/knowledge', { params: { type } });

export const addKnowledge = (data: {
  type: string; title: string; content: string; tags: string[]
}) => api.post('/knowledge', data);

export const deleteKnowledge = (id: string) =>
  api.delete(`/knowledge/${id}`);

export const updateKnowledgeStatus = (id: string, status: string) =>
  api.patch(`/knowledge/${id}/status`, { status });
