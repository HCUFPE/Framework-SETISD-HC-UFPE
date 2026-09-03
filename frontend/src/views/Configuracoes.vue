<template>
  <div class="space-y-6">
    <!-- Cabeçalho das Configurações -->
    <Card>
      <template #header>
        <div class="flex items-center space-x-3">
          <Cog6ToothIcon class="h-7 w-7 text-paper-text" />
          <h1 class="text-2xl font-bold text-paper-text">Configurações</h1>
        </div>
      </template>

      <div v-if="authStore.isAdmin" class="space-y-6">
        <p class="text-gray-600 leading-relaxed">
          Gerencie o seu perfil corporativo, o cadastro de usuários autorizados e a atribuição de perfis de acesso (RBAC) do **Framework-SETISD-HC-UFPE**.
        </p>

        <!-- 1. Perfil do Usuário Logado -->
        <div v-if="authStore.user" class="p-5 bg-white border border-gray-200 rounded-xl shadow-sm space-y-3">
          <div class="flex items-center space-x-2 text-paper-text font-bold text-lg border-b pb-2">
            <UserCircleIcon class="h-6 w-6 text-gray-500" />
            <span>Seu Perfil Corporativo (Active Directory)</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm pt-1">
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">Usuário / Login AD</p>
              <p class="font-bold text-gray-800">{{ authStore.user.username }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">Nome Completo</p>
              <p class="font-medium text-gray-800">{{ authStore.user.displayName?.[0] || authStore.user.username }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">E-mail Corporativo</p>
              <p class="font-medium text-gray-800">{{ authStore.user.email?.[0] || 'Não cadastrado' }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">Setor / Departamento</p>
              <p class="font-medium text-gray-800">{{ authStore.user.department?.[0] || 'SETISD / HC-UFPE' }}</p>
            </div>
          </div>
        </div>

        <!-- 2. Painel de Gestão de Usuários e Perfis (RBAC Local) -->
        <div class="p-5 bg-white border border-gray-200 rounded-xl shadow-sm space-y-4">
          <div class="flex flex-col md:flex-row md:items-center justify-between border-b pb-3 gap-3">
            <div>
              <h2 class="text-lg font-bold text-paper-text flex items-center gap-2">
                <UserGroupIcon class="h-6 w-6 text-gray-600" />
                Usuários Autorizados no Sistema (RBAC Local)
              </h2>
              <p class="text-xs text-gray-500 mt-0.5">
                Inclua o login do Active Directory (AD) de um funcionário para autorizar o acesso a este sistema.
              </p>
            </div>
            <Button variant="primary" @click="showAddUserModal = true">
              <template #icon>
                <UserPlusIcon class="h-5 w-5" />
              </template>
              Incluir Usuário
            </Button>
          </div>

          <!-- Tabela de Usuários Cadastrados -->
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-gray-600">
              <thead class="bg-gray-50 text-xs uppercase font-semibold text-gray-500 border-b">
                <tr>
                  <th class="py-3 px-4">Login AD</th>
                  <th class="py-3 px-4">Nome do Colaborador</th>
                  <th class="py-3 px-4">Perfil de Acesso (Role)</th>
                  <th class="py-3 px-4 text-center">Status</th>
                  <th class="py-3 px-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="user in usersList" :key="user.id" class="hover:bg-gray-50/80 transition-colors">
                  <td class="py-3 px-4 font-bold text-gray-800 flex items-center gap-2">
                    <UserIcon class="h-4 w-4 text-gray-400" />
                    {{ user.username }}
                  </td>
                  <td class="py-3 px-4 font-medium text-gray-700">{{ user.nome }}</td>
                  <td class="py-3 px-4">
                    <span :class="getRoleBadgeClass(user.perfil)" class="px-2.5 py-1 text-xs font-bold rounded-md">
                      {{ user.perfil }}
                    </span>
                  </td>
                  <td class="py-3 px-4 text-center">
                    <span :class="user.ativo ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'" class="px-2 py-0.5 text-xs font-bold rounded">
                      {{ user.ativo ? 'ATIVO' : 'INATIVO' }}
                    </span>
                  </td>
                  <td class="py-3 px-4 text-right space-x-2">
                    <button 
                      @click="openEditModal(user)" 
                      title="Alterar Perfil" 
                      class="px-2.5 py-1 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-md transition"
                    >
                      Alterar Perfil
                    </button>
                    <button 
                      @click="toggleUserStatus(user)" 
                      :class="user.ativo ? 'text-red-600 hover:bg-red-50 border-red-200' : 'text-emerald-600 hover:bg-emerald-50 border-emerald-200'"
                      class="px-2.5 py-1 text-xs font-semibold border rounded-md transition"
                    >
                      {{ user.ativo ? 'Inativar' : 'Ativar' }}
                    </button>
                    <button 
                      @click="removeUser(user.id)" 
                      title="Excluir Usuário"
                      class="px-2 py-1 text-xs font-semibold text-red-500 hover:text-red-700 hover:bg-red-50 rounded-md transition"
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 3. Guias e Exemplos de Perfis (Informativo) -->
        <div class="p-5 bg-gray-50 border border-gray-200 rounded-xl space-y-3">
          <div class="flex items-center space-x-2 text-paper-text font-bold text-md border-b pb-2">
            <ShieldCheckIcon class="h-5 w-5 text-gray-600" />
            <span>Exemplos de Perfis Disponíveis para Atribuição</span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-1">
            <div 
              v-for="roleItem in availableRoles" 
              :key="roleItem.nome"
              class="p-3 bg-white border border-gray-200 rounded-lg space-y-1"
            >
              <span :class="roleItem.badgeClass" class="px-2 py-0.5 text-xs font-bold rounded">
                {{ roleItem.nome }}
              </span>
              <p class="text-xs text-gray-500 pt-1 leading-relaxed">{{ roleItem.descricao }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl">
        <h2 class="text-lg font-bold">Acesso Restrito</h2>
        <p class="text-sm mt-1">Você precisa de privilégios de administrador para visualizar as configurações avançadas.</p>
      </div>
    </Card>

    <!-- Modal 1: Incluir Novo Usuário AD -->
    <Modal :show="showAddUserModal" @close="closeAddModal">
      <template #header>Incluir Usuário no Sistema (AD)</template>
      <form @submit.prevent="saveUser" class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1">Login do AD (Usuário)</label>
          <input 
            v-model="newUser.username" 
            type="text" 
            required 
            placeholder="Ex: daniel.turmina ou 1234567"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-paper-text focus:outline-none text-sm"
          />
          <p class="text-xs text-gray-400 mt-1">Digite a conta corporativa da Ebserh (ex: `daniel.turmina`).</p>
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1">Nome Completo do Colaborador</label>
          <input 
            v-model="newUser.nome" 
            type="text" 
            required 
            placeholder="Ex: Daniel Freire Turmina"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-paper-text focus:outline-none text-sm"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1">Perfil de Acesso (Role)</label>
          <select 
            v-model="newUser.perfil" 
            required 
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-paper-text focus:outline-none text-sm bg-white"
          >
            <option value="" disabled>Selecione um perfil...</option>
            <option v-for="role in availableRoles" :key="role.nome" :value="role.nome">
              {{ role.nome }} — {{ role.descricao }}
            </option>
          </select>
        </div>

        <div class="flex justify-end space-x-3 pt-4 border-t">
          <Button variant="secondary" type="button" @click="closeAddModal">Cancelar</Button>
          <Button variant="primary" type="submit">Incluir Usuário</Button>
        </div>
      </form>
    </Modal>

    <!-- Modal 2: Alterar Perfil do Usuário -->
    <Modal :show="showEditUserModal" @close="closeEditModal">
      <template #header>Alterar Perfil de Acesso</template>
      <form v-if="editingUser" @submit.prevent="updateUserRole" class="space-y-4">
        <div class="p-3 bg-gray-50 border rounded-lg space-y-1 text-sm">
          <p><strong class="text-gray-700">Login AD:</strong> <span class="font-bold text-gray-900">{{ editingUser.username }}</span></p>
          <p><strong class="text-gray-700">Nome:</strong> {{ editingUser.nome }}</p>
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1">Selecione o Novo Perfil de Acesso</label>
          <select 
            v-model="editingUser.perfil" 
            required 
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-paper-text focus:outline-none text-sm bg-white"
          >
            <option v-for="role in availableRoles" :key="role.nome" :value="role.nome">
              {{ role.nome }} — {{ role.descricao }}
            </option>
          </select>
        </div>

        <div class="flex justify-end space-x-3 pt-4 border-t">
          <Button variant="secondary" type="button" @click="closeEditModal">Cancelar</Button>
          <Button variant="primary" type="submit">Salvar Perfil</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Card from '../components/Card.vue';
import Modal from '../components/Modal.vue';
import Button from '../components/Button.vue';
import { useAuthStore } from '../stores/auth';
import { 
  Cog6ToothIcon, 
  UserCircleIcon, 
  ShieldCheckIcon, 
  UserGroupIcon, 
  UserPlusIcon, 
  UserIcon 
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore();
const showAddUserModal = ref(false);
const showEditUserModal = ref(false);

interface UserRBAC {
  id: number;
  username: string;
  nome: string;
  perfil: string;
  ativo: boolean;
}

const availableRoles = [
  { nome: 'ADMINISTRADOR', descricao: 'Gestão total do sistema, configurações e concessão de perfis.', badgeClass: 'bg-purple-100 text-purple-800' },
  { nome: 'MEDICO', descricao: 'Acesso a evolução clínica, prescrições e altas hospitalares.', badgeClass: 'bg-blue-100 text-blue-800' },
  { nome: 'ENFERMAGEM', descricao: 'Acesso ao censo diário de leitos, checagem e sinais vitais.', badgeClass: 'bg-emerald-100 text-emerald-800' },
  { nome: 'FARMACEUTICO', descricao: 'Acesso à dispensação de medicamentos e controle de estoque.', badgeClass: 'bg-amber-100 text-amber-800' },
  { nome: 'GESTOR_UNIDADE', descricao: 'Acesso a relatórios estratégicos, indicadores e dashboards do setor.', badgeClass: 'bg-indigo-100 text-indigo-800' },
  { nome: 'CONSULTA', descricao: 'Acesso estritamente somente-leitura (Read-Only) para auditoria.', badgeClass: 'bg-gray-100 text-gray-800' }
];

// Lista Inicial Simulada de Usuários RBAC Autorizados no Banco Local (data/app.db)
const usersList = ref<UserRBAC[]>([
  { id: 1, username: 'admin', nome: 'Administrador do Sistema', perfil: 'ADMINISTRADOR', ativo: true },
  { id: 2, username: 'gestor.unidade', nome: 'Gestor da Unidade', perfil: 'GESTOR_UNIDADE', ativo: true },
  { id: 3, username: 'medico.exemplo', nome: 'Médico do Setor', perfil: 'MEDICO', ativo: true },
  { id: 4, username: 'enfermeiro.exemplo', nome: 'Enfermeiro do Setor', perfil: 'ENFERMAGEM', ativo: true },
  { id: 5, username: 'farmaceutico.exemplo', nome: 'Farmacêutico do Setor', perfil: 'FARMACEUTICO', ativo: true },
  { id: 6, username: 'usuario.consulta', nome: 'Usuário de Consulta', perfil: 'CONSULTA', ativo: false }
]);

const newUser = ref({
  username: '',
  nome: '',
  perfil: 'CONSULTA'
});

const editingUser = ref<UserRBAC | null>(null);

const getRoleBadgeClass = (perfil: string) => {
  const role = availableRoles.find(r => r.nome === perfil);
  return role ? role.badgeClass : 'bg-gray-100 text-gray-700';
};

const closeAddModal = () => {
  showAddUserModal.value = false;
  newUser.value = { username: '', nome: '', perfil: 'CONSULTA' };
};

const closeEditModal = () => {
  showEditUserModal.value = false;
  editingUser.value = null;
};

const saveUser = () => {
  if (!newUser.value.username || !newUser.value.nome) return;

  usersList.value.push({
    id: Date.now(),
    username: newUser.value.username.trim().toLowerCase(),
    nome: newUser.value.nome.trim(),
    perfil: newUser.value.perfil,
    ativo: true
  });

  closeAddModal();
};

const openEditModal = (user: UserRBAC) => {
  editingUser.value = { ...user };
  showEditUserModal.value = true;
};

const updateUserRole = () => {
  if (!editingUser.value) return;

  const index = usersList.value.findIndex(u => u.id === editingUser.value?.id);
  if (index !== -1) {
    usersList.value[index].perfil = editingUser.value.perfil;
  }

  closeEditModal();
};

const toggleUserStatus = (user: UserRBAC) => {
  user.ativo = !user.ativo;
};

const removeUser = (userId: number) => {
  usersList.value = usersList.value.filter(u => u.id !== userId);
};
</script>
