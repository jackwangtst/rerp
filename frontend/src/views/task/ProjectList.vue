<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi, type ProjectListItem } from '@/api/project'
import { contractApi, type ContractListItem } from '@/api/contract'
import { customerApi, type CustomerListItem } from '@/api/customer'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const list = ref<ProjectListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  contract_id: '',
  customer_id: '',
  standard: '',
  certification_scope: '',
  phase: '初审',
  project_manager: '',
  planned_start_date: '',
  planned_end_date: '',
  status: '筹备中',
  progress: 0,
})
const editId = ref<string | null>(null)
const saving = ref(false)

const statusOptions = ['筹备中', '进行中', '已完成', '已取消']
const phaseOptions = ['初审', '监督审核', '再认证']

// 合同搜索
const contractOptions = ref<ContractListItem[]>([])
const contractLoading = ref(false)
async function searchContracts(keyword: string) {
  if (!keyword) return
  contractLoading.value = true
  try {
    const res = await contractApi.list({ keyword, page_size: 20 })
    contractOptions.value = res.data
    // 选择合同时自动带入客户ID
  } finally {
    contractLoading.value = false
  }
}
function onContractSelect(contractId: string) {
  const c = contractOptions.value.find(c => c.id === contractId)
  if (c) form.customer_id = c.customer_id
}

// 客户搜索（仅编辑时用于回显）
const customerOptions = ref<CustomerListItem[]>([])

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await projectApi.list(params as any)
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.status = ''; query.keyword = ''; query.page = 1; loadList() }

function openCreate() {
  editId.value = null
  contractOptions.value = []
  customerOptions.value = []
  Object.assign(form, {
    contract_id: '', customer_id: '', standard: '', certification_scope: '',
    phase: '初审', project_manager: authStore.user?.id ?? '',
    planned_start_date: '', planned_end_date: '', status: '筹备中', progress: 0,
  })
  dialogVisible.value = true
}

async function openEdit(row: ProjectListItem) {
  editId.value = row.id
  const [cRes, cuRes] = await Promise.all([
    contractApi.list({ keyword: '', page_size: 50 }),
    customerApi.list({ keyword: '', page_size: 50 }),
  ])
  contractOptions.value = cRes.data
  customerOptions.value = cuRes.data
  Object.assign(form, {
    contract_id: row.contract_id,
    customer_id: row.customer_id,
    standard: row.standard,
    certification_scope: row.certification_scope,
    phase: row.phase,
    project_manager: row.project_manager,
    planned_start_date: row.planned_start_date ?? '',
    planned_end_date: row.planned_end_date ?? '',
    status: row.status,
    progress: row.progress,
  })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: Record<string, unknown> = { ...form }
    if (!payload.planned_start_date) payload.planned_start_date = null
    if (!payload.planned_end_date) payload.planned_end_date = null
    if (editId.value) {
      await projectApi.update(editId.value, payload)
      ElMessage.success('更新成功')
      dialogVisible.value = false
      loadList()
    } else {
      const res = await projectApi.create(payload)
      dialogVisible.value = false
      router.push(`/projects/${res.data.id}`)
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: ProjectListItem) {
  await ElMessageBox.confirm(`确认删除项目「${row.project_no}」？`, '提示', { type: 'warning' })
  await projectApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

const statusTagType = (s: string) =>
  ({ '筹备中': 'info', '进行中': 'primary', '已完成': 'success', '已取消': 'danger' }[s] ?? '') as any

function goDetail(row: ProjectListItem) {
  router.push(`/projects/${row.id}`)
}

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="7">
          <el-input v-model="query.keyword" placeholder="搜索项目编号/标准/范围" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="query.status" placeholder="状态" clearable style="width:100%">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button type="primary" icon="Plus" @click="openCreate">新建项目</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id" style="cursor:pointer" @row-click="goDetail">
        <el-table-column prop="project_no" label="项目编号" width="150" />
        <el-table-column prop="standard" label="认证标准" width="150" show-overflow-tooltip />
        <el-table-column prop="certification_scope" label="认证范围" min-width="180" show-overflow-tooltip />
        <el-table-column prop="phase" label="阶段" width="90" />
        <el-table-column prop="planned_start_date" label="计划开始" width="110" />
        <el-table-column prop="planned_end_date" label="计划完成" width="110" />
        <el-table-column prop="progress" label="进度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click.stop="openEdit(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click.stop="handleDelete(row)">删除</el-button>
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

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑项目' : '新建认证项目'" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="90px" :rules="{
        contract_id: [{ required: true, message: '请选择关联合同' }],
        standard: [{ required: true, message: '请输入认证标准' }],
        certification_scope: [{ required: true, message: '请输入认证范围' }],
      }">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="关联合同" prop="contract_id">
              <el-select
                v-model="form.contract_id"
                filterable remote
                :remote-method="searchContracts"
                :loading="contractLoading"
                placeholder="输入合同名称/编号搜索"
                style="width:100%"
                @change="onContractSelect"
              >
                <el-option
                  v-for="c in contractOptions"
                  :key="c.id"
                  :label="`${c.contract_no} ${c.contract_name}`"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="阶段">
              <el-select v-model="form.phase" style="width:100%">
                <el-option v-for="p in phaseOptions" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="认证标准" prop="standard">
              <el-input v-model="form.standard" placeholder="如 ISO9001:2015" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="认证范围" prop="certification_scope">
              <el-input v-model="form.certification_scope" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划开始">
              <el-date-picker v-model="form.planned_start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划完成">
              <el-date-picker v-model="form.planned_end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="进度(%)">
              <el-slider v-model="form.progress" :min="0" :max="100" show-input style="padding-right:12px" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
