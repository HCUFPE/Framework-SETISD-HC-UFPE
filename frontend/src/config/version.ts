/**
 * Single Source of Truth Version Store (Frontend)
 * Carrega a versão e metadados do sistema dinamicamente a partir do Backend (/api/health).
 * Você SÓ PRECISA alterar a versão no arquivo backend 'src/version.py'.
 */
import { ref } from 'vue';
import api from '../services/api';

export const APP_VERSION = ref('1.0.0');
export const APP_NAME = ref('Framework SETISD');
export const SYSTEM_TITLE = ref('Nome do Sistema');
export const HOSPITAL_NAME = ref('Hospital das Clínicas da UFPE (HC-UFPE / EBSERH)');
export const DEPARTMENT_NAME = ref('Setor de Tecnologia da Informação e Saúde Digital — SETISD');

export async function fetchSystemConfig() {
  try {
    const response = await api.get('/api/health');
    if (response.data) {
      if (response.data.version) APP_VERSION.value = response.data.version;
      if (response.data.app_name) APP_NAME.value = response.data.app_name;
      if (response.data.system_title) SYSTEM_TITLE.value = response.data.system_title;
      if (response.data.organization) HOSPITAL_NAME.value = response.data.organization;
      if (response.data.department) DEPARTMENT_NAME.value = response.data.department;
    }
  } catch (error) {
    // Mantém fallbacks caso a API ainda esteja iniciando
  }
}

// Inicialização automática ao carregar o frontend
fetchSystemConfig();
