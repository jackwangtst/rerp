<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { customerApi, type CustomerListItem } from '@/api/customer'

const router = useRouter()

const loading = ref(false)
const list = ref<CustomerListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  company_name: '',
  company_short_name: '',
  industry: '',
  company_size: '',
  province: '',
  city: '',
  address: '',
  customer_level: '',
  status: '潜在',
  legal_representative: '',
  unified_social_credit_code: '',
  remark: '',
  contacts: [] as { name: string; phone: string; title: string; is_primary: boolean }[],
})
const editId = ref<string | null>(null)
const saving = ref(false)

const statusOptions = ['潜在', '在服务', '已到期', '已流失']
const levelOptions = ['A', 'B', 'C']
const sizeOptions = ['小微', '中', '大']

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await customerApi.list(params as any)
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
  Object.assign(form, {
    company_name: '', company_short_name: '', industry: '', company_size: '',
    province: '', city: '', address: '', customer_level: '', status: '潜在',
    legal_representative: '', unified_social_credit_code: '', remark: '',
    contacts: [{ name: '', phone: '', title: '', is_primary: true }],
  })
  dialogVisible.value = true
}

async function openEdit(row: CustomerListItem) {
  const res = await customerApi.get(row.id)
  const d = res.data
  editId.value = d.id
  Object.assign(form, {
    company_name: d.company_name, company_short_name: d.company_short_name ?? '',
    industry: d.industry ?? '', company_size: d.company_size ?? '',
    province: d.province ?? '', city: d.city ?? '',
    address: d.address ?? '',
    customer_level: d.customer_level ?? '', status: d.status,
    legal_representative: d.legal_representative ?? '',
    unified_social_credit_code: d.unified_social_credit_code ?? '',
    remark: d.remark ?? '',
    contacts: d.contacts.map(c => ({ name: c.name, phone: c.phone, title: c.title ?? '', is_primary: c.is_primary })),
  })
  dialogVisible.value = true
}

function addContact() { form.contacts.push({ name: '', phone: '', title: '', is_primary: false }) }
function removeContact(i: number) { form.contacts.splice(i, 1) }

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editId.value) {
      await customerApi.update(editId.value, { ...form })
      ElMessage.success('更新成功')
    } else {
      await customerApi.create({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: CustomerListItem) {
  await ElMessageBox.confirm(`确认删除客户「${row.company_name}」？`, '提示', { type: 'warning' })
  await customerApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

function goDetail(row: CustomerListItem) { router.push(`/customers/${row.id}`) }

const statusTagType = (s: string) =>
  ({ '潜在': 'info', '在服务': 'success', '已到期': 'warning', '已流失': 'danger' }[s] ?? 'info') as any

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="6">
          <el-input v-model="query.keyword" placeholder="搜索公司名称" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="query.status" placeholder="客户状态" clearable style="width:100%">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button type="primary" icon="Plus" @click="openCreate">新建客户</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id" @row-click="goDetail" style="cursor:pointer">
        <el-table-column prop="customer_no" label="客户编号" width="140" />
        <el-table-column prop="company_name" label="公司名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="industry" label="行业" width="120" show-overflow-tooltip />
        <el-table-column prop="province" label="省份" width="90" />
        <el-table-column prop="city" label="城市" width="90" />
        <el-table-column prop="customer_level" label="等级" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.customer_level" size="small">{{ row.customer_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="120">
          <template #default="{ row }">{{ row.created_at.slice(0, 10) }}</template>
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
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑客户' : '新建客户'" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="110px" :rules="{
        company_name: [{ required: true, message: '请输入公司名称' }],
      }">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="公司全称" prop="company_name">
              <el-input v-model="form.company_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司简称">
              <el-input v-model="form.company_short_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="行业">
              <el-input v-model="form.industry" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="规模">
              <el-select v-model="form.company_size" clearable style="width:100%">
                <el-option v-for="s in sizeOptions" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="省份">
              <el-input v-model="form.province" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="城市">
              <el-input v-model="form.city" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="收件地址">
              <el-input v-model="form.address" placeholder="详细收件地址（将用于报价单自动填充）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户等级">
              <el-select v-model="form.customer_level" clearable style="width:100%">
                <el-option v-for="l in levelOptions" :key="l" :label="l" :value="l" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="法定代表人">
              <el-input v-model="form.legal_representative" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="统一信用代码">
              <el-input v-model="form.unified_social_credit_code" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">联系人</el-divider>
        <div v-for="(c, i) in form.contacts" :key="i"
          style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
          <el-input v-model="c.name" placeholder="姓名" style="width:90px" />
          <el-input v-model="c.phone" placeholder="电话" style="width:130px" />
          <el-input v-model="c.title" placeholder="职务" style="width:90px" />
          <el-checkbox v-model="c.is_primary">主要</el-checkbox>
          <el-button link type="danger" icon="Delete" @click="removeContact(i)"
            :disabled="form.contacts.length === 1" />
        </div>
        <el-button size="small" icon="Plus" @click="addContact">添加联系人</el-button>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
