<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi, type UserOut } from '@/api/users'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const loading = ref(false)
const list = ref<UserOut[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20 })

const dialogVisible = ref(false)
const formRef = ref()
const editId = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  username: '',
  full_name: '',
  password: '',
  role: 'ROLE_USER',
  email: '',
  phone: '',
  is_active: true,
})

const roleOptions = [
  { label: '管理员', value: 'ROLE_ADMIN' },
  { label: '普通用户', value: 'ROLE_USER' },
]

const roleLabel = (role: string) =>
  roleOptions.find(r => r.value === role)?.label ?? role

async function loadList() {
  loading.value = true
  try {
    const res = await userApi.list({ page: query.page, page_size: query.page_size })
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editId.value = null
  Object.assign(form, {
    username: '', full_name: '', password: '',
    role: 'ROLE_USER', email: '', phone: '', is_active: true,
  })
  dialogVisible.value = true
}

function openEdit(row: UserOut) {
  editId.value = row.id
  Object.assign(form, {
    username: row.username,
    full_name: row.full_name,
    password: '',
    role: row.role,
    email: row.email ?? '',
    phone: row.phone ?? '',
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editId.value) {
      const payload: Record<string, unknown> = {
        full_name: form.full_name,
        role: form.role,
        email: form.email || null,
        phone: form.phone || null,
        is_active: form.is_active,
      }
      if (form.password) payload.password = form.password
      await userApi.update(editId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await userApi.create({
        username: form.username,
        full_name: form.full_name,
        password: form.password,
        role: form.role,
        email: form.email || undefined,
        phone: form.phone || undefined,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function toggleActive(row: UserOut) {
  await userApi.update(row.id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '已禁用' : '已启用')
  loadList()
}

async function handleDelete(row: UserOut) {
  await ElMessageBox.confirm(`确认删除用户「${row.full_name}」？`, '提示', { type: 'warning' })
  await userApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row align="middle">
        <el-col :span="16">
          <span style="font-size:15px;font-weight:500">用户管理</span>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button type="primary" icon="Plus" @click="openCreate">新建用户</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id">
        <el-table-column prop="username" label="用户名" width="130" />
        <el-table-column prop="full_name" label="姓名" width="100" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'ROLE_ADMIN' ? 'danger' : 'info'" size="small">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="160">
          <template #default="{ row }">
            {{ row.last_login ? row.last_login.slice(0, 16).replace('T', ' ') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" link :type="row.is_active ? 'warning' : 'success'"
              :disabled="row.id === authStore.user?.id"
              @click="toggleActive(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" link type="danger"
              :disabled="row.id === authStore.user?.id"
              @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:16px;justify-content:flex-end;display:flex"
        @change="loadList"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑用户' : '新建用户'" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="80px" :rules="{
        username: [{ required: true, message: '请输入用户名' }],
        full_name: [{ required: true, message: '请输入姓名' }],
        password: editId ? [] : [{ required: true, message: '请输入初始密码' }],
      }">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editId" placeholder="登录账号" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item :label="editId ? '新密码' : '初始密码'" prop="password">
          <el-input v-model="form.password" type="password" show-password
            :placeholder="editId ? '不填则不修改密码' : '请输入初始密码'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item v-if="editId" label="状态">
          <el-switch v-model="form.is_active" active-text="正常" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
