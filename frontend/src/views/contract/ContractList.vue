<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contractApi, type ContractListItem } from '@/api/contract'
import { customerApi, type CustomerListItem } from '@/api/customer'
import { oppApi, type OppListItem } from '@/api/opportunity'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const list = ref<ContractListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

// ── 新建/编辑 ────────────────────────────────────────────────
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  customer_id: '',
  opp_id: '',
  contract_name: '',
  contract_type: '新签',
  certification_standard: '',
  service_scope: '',
  total_amount: 0,
  tax_rate: 6,
  sign_date: '',
  start_date: '',
  end_date: '',
  status: '草稿',
  remark: '',
  sales_person: '',
  items: [] as { item_name: string; standard: string; audit_days: number | null; unit_price: number; quantity: number; discount: number; amount: number; item_type: string }[],
  payment_plans: [] as { installment_no: number; description: string; plan_amount: number; due_date: string; status: string }[],
})
const editId = ref<string | null>(null)
const saving = ref(false)

// 客户搜索
const customerOptions = ref<CustomerListItem[]>([])
const customerLoading = ref(false)
async function searchCustomers(keyword: string) {
  if (!keyword) return
  customerLoading.value = true
  try {
    const res = await customerApi.list({ keyword, page_size: 20 })
    customerOptions.value = res.data
  } finally {
    customerLoading.value = false
  }
}

// 商机搜索
const oppOptions = ref<OppListItem[]>([])
const oppLoading = ref(false)
async function searchOpps(keyword: string) {
  if (!keyword) return
  oppLoading.value = true
  try {
    const res = await oppApi.list({ keyword, page_size: 20 })
    oppOptions.value = res.data
  } finally {
    oppLoading.value = false
  }
}

const statusOptions = ['草稿', '审批中', '待签署', '执行中', '已完成', '已终止']
const contractTypeOptions = ['新签', '续签', '变更', '补充协议']

const totalFromItems = computed(() =>
  form.items.reduce((s, i) => s + (i.amount || 0), 0)
)

function recalcItem(item: typeof form.items[0]) {
  item.amount = Math.round(item.quantity * item.unit_price * item.discount * 100) / 100
}

function addItem() {
  form.items.push({ item_name: '', standard: '', audit_days: null, unit_price: 0, quantity: 1, discount: 1, amount: 0, item_type: '' })
}
function removeItem(i: number) { form.items.splice(i, 1) }

function addPlan() {
  const no = form.payment_plans.length + 1
  form.payment_plans.push({ installment_no: no, description: no === 1 ? '首付款' : '尾款', plan_amount: 0, due_date: '', status: '待支付' })
}
function removePlan(i: number) {
  form.payment_plans.splice(i, 1)
  form.payment_plans.forEach((p, idx) => { p.installment_no = idx + 1 })
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await contractApi.list(params as any)
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
  customerOptions.value = []
  oppOptions.value = []
  Object.assign(form, {
    customer_id: '', opp_id: '', contract_name: '', contract_type: '新签',
    certification_standard: '', service_scope: '', total_amount: 0, tax_rate: 6,
    sign_date: '', start_date: '', end_date: '', status: '草稿', remark: '',
    sales_person: authStore.user?.id ?? '',
    items: [{ item_name: '', standard: '', audit_days: null, unit_price: 0, quantity: 1, discount: 1, amount: 0, item_type: '' }],
    payment_plans: [{ installment_no: 1, description: '首付款', plan_amount: 0, due_date: '', status: '待支付' }],
  })
  dialogVisible.value = true
}

async function openEdit(row: ContractListItem) {
  const res = await contractApi.get(row.id)
  const d = res.data
  editId.value = d.id
  // 预加载客户和商机列表，让选择器能显示已选项的名称
  const [cRes, oRes] = await Promise.all([
    customerApi.list({ keyword: '', page_size: 50 }),
    oppApi.list({ keyword: '', page_size: 50 }),
  ])
  customerOptions.value = cRes.data
  oppOptions.value = oRes.data
  Object.assign(form, {
    customer_id: d.customer_id, opp_id: d.opp_id ?? '',
    contract_name: d.contract_name, contract_type: d.contract_type,
    certification_standard: d.certification_standard, service_scope: d.service_scope,
    total_amount: d.total_amount, tax_rate: d.tax_rate ?? 6,
    sign_date: d.sign_date ?? '', start_date: d.start_date ?? '', end_date: d.end_date ?? '',
    status: d.status, remark: d.remark ?? '',
    sales_person: d.sales_person,
    items: d.items.map(i => ({ ...i })),
    payment_plans: d.payment_plans.map(p => ({ ...p })),
  })
  dialogVisible.value = true
}

function goDetail(row: ContractListItem) { router.push(`/contracts/${row.id}`) }

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: Record<string, unknown> = { ...form, total_amount: totalFromItems.value || form.total_amount }
    for (const k of ['opp_id', 'sign_date', 'start_date', 'end_date'] as const) {
      if (!payload[k]) payload[k] = null
    }
    // Normalize payment plan due_date: empty string → null
    const plans = (payload.payment_plans as any[]) ?? []
    payload.payment_plans = plans.map(p => ({ ...p, due_date: p.due_date || null }))
    if (editId.value) {
      await contractApi.update(editId.value, payload)
      ElMessage.success('更新成功')
      dialogVisible.value = false
      loadList()
    } else {
      const res = await contractApi.create(payload)
      dialogVisible.value = false
      router.push(`/contracts/${res.data.id}`)
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: ContractListItem) {
  await ElMessageBox.confirm(`确认删除合同「${row.contract_name}」？`, '提示', { type: 'warning' })
  await contractApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

const statusTagType = (s: string) =>
  ({ '草稿': 'info', '审批中': 'warning', '待签署': 'warning', '执行中': 'primary',
     '已完成': 'success', '已终止': 'danger' }[s] ?? '') as any

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="7">
          <el-input v-model="query.keyword" placeholder="搜索合同名称/编号" clearable @keyup.enter="handleSearch" />
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
          <el-button type="primary" icon="Plus" @click="openCreate">新建合同</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id" @row-click="goDetail" style="cursor:pointer">
        <el-table-column prop="contract_no" label="合同编号" width="150" />
        <el-table-column prop="contract_name" label="合同名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="contract_type" label="类型" width="90" />
        <el-table-column prop="certification_standard" label="认证标准" width="140" show-overflow-tooltip />
        <el-table-column prop="total_amount" label="合同金额" width="120" align="right">
          <template #default="{ row }">{{ Number(row.total_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="sign_date" label="签署日期" width="110" />
        <el-table-column prop="end_date" label="到期日期" width="110" />
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
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑合同' : '新建合同'" width="900px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="100px" :rules="{
        customer_id: [{ required: true, message: '请选择客户' }],
        contract_name: [{ required: true, message: '请输入合同名称' }],
        certification_standard: [{ required: true, message: '请输入认证标准' }],
        service_scope: [{ required: true, message: '请输入服务范围' }],
      }">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="合同名称" prop="contract_name">
              <el-input v-model="form.contract_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户" prop="customer_id">
              <el-select
                v-model="form.customer_id"
                filterable
                remote
                :remote-method="searchCustomers"
                :loading="customerLoading"
                placeholder="输入客户名称搜索"
                style="width:100%"
                value-key="id"
              >
                <el-option
                  v-for="c in customerOptions"
                  :key="c.id"
                  :label="c.company_name"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联商机">
              <el-select
                v-model="form.opp_id"
                filterable
                remote
                clearable
                :remote-method="searchOpps"
                :loading="oppLoading"
                placeholder="输入商机名称搜索（选填）"
                style="width:100%"
              >
                <el-option
                  v-for="o in oppOptions"
                  :key="o.id"
                  :label="o.opp_name"
                  :value="o.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同类型">
              <el-select v-model="form.contract_type" style="width:100%">
                <el-option v-for="t in contractTypeOptions" :key="t" :label="t" :value="t" />
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
            <el-form-item label="认证标准" prop="certification_standard">
              <el-input v-model="form.certification_standard" placeholder="如 ISO9001:2015" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率(%)">
              <el-input-number v-model="form.tax_rate" :min="0" :max="100" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="签署日期">
              <el-date-picker v-model="form.sign_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开始日期">
              <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="到期日期">
              <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="服务范围" prop="service_scope">
              <el-input v-model="form.service_scope" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">服务明细</el-divider>
        <el-table :data="form.items" size="small" border>
          <el-table-column label="服务名称" min-width="130">
            <template #default="{ row }"><el-input v-model="row.item_name" size="small" /></template>
          </el-table-column>
          <el-table-column label="标准" width="110">
            <template #default="{ row }"><el-input v-model="row.standard" size="small" /></template>
          </el-table-column>
          <el-table-column label="人天" width="90">
            <template #default="{ row }">
              <el-input-number v-model="row.audit_days" :min="0" :precision="1" size="small" style="width:80px" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" style="width:110px"
                @change="recalcItem(row)" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="90">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="0" :precision="2" size="small" style="width:80px"
                @change="recalcItem(row)" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="折扣" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.discount" :min="0" :max="1" :step="0.05" :precision="4" size="small"
                style="width:90px" @change="recalcItem(row)" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="100" align="right">
            <template #default="{ row }">{{ row.amount.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="" width="50" align="center">
            <template #default="{ $index }">
              <el-button link type="danger" icon="Delete" @click="removeItem($index)"
                :disabled="form.items.length === 1" />
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top:6px;display:flex;justify-content:space-between;align-items:center">
          <el-button size="small" icon="Plus" @click="addItem">添加明细</el-button>
          <span style="font-size:13px;font-weight:600">
            合计：<span style="color:#409eff">{{ totalFromItems.toLocaleString() }}</span> 元
          </span>
        </div>

        <el-divider content-position="left">付款计划</el-divider>
        <el-table :data="form.payment_plans" size="small" border>
          <el-table-column prop="installment_no" label="期次" width="60" align="center" />
          <el-table-column label="说明" width="120">
            <template #default="{ row }"><el-input v-model="row.description" size="small" /></template>
          </el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.plan_amount" :min="0" :precision="2" size="small" style="width:110px" />
            </template>
          </el-table-column>
          <el-table-column label="应付日期" width="140">
            <template #default="{ row }">
              <el-date-picker v-model="row.due_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:130px" />
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-select v-model="row.status" size="small" style="width:80px">
                <el-option label="待支付" value="待支付" />
                <el-option label="部分支付" value="部分支付" />
                <el-option label="已支付" value="已支付" />
                <el-option label="已逾期" value="已逾期" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="" width="50" align="center">
            <template #default="{ $index }">
              <el-button link type="danger" icon="Delete" @click="removePlan($index)" />
            </template>
          </el-table-column>
        </el-table>
        <el-button size="small" icon="Plus" style="margin-top:6px" @click="addPlan">添加付款期</el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
