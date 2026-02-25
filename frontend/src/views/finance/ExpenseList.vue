<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { expenseApi, type ExpenseListItem, type ExpenseStats } from '@/api/expense'

const EXPENSE_TYPES = ['认证费', '差旅', '代理费', '测试费', '其他']

// ── 列表 ─────────────────────────────────────────────────────
const loading = ref(false)
const list = ref<ExpenseListItem[]>([])
const total = ref(0)
const query = reactive({
  page: 1,
  page_size: 20,
  expense_type: '',
  date_from: '',
  date_to: '',
})

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.expense_type) params.expense_type = query.expense_type
    if (query.date_from) params.date_from = query.date_from
    if (query.date_to) params.date_to = query.date_to
    const res = await expenseApi.list(params)
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() {
  query.expense_type = ''
  query.date_from = ''
  query.date_to = ''
  query.page = 1
  loadList()
}

// ── 统计 ─────────────────────────────────────────────────────
const stats = ref<ExpenseStats | null>(null)
async function loadStats() {
  const params: Record<string, unknown> = {}
  if (query.date_from) params.date_from = query.date_from
  if (query.date_to) params.date_to = query.date_to
  stats.value = await expenseApi.stats(params)
}

// ── 弹窗 ─────────────────────────────────────────────────────
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({
  expense_type: '认证费',
  amount: 0,
  vendor: '',
  paid_at: '',
  contract_id: '',
  customer_id: '',
  remark: '',
})

function openCreate() {
  editingId.value = null
  form.expense_type = '认证费'
  form.amount = 0
  form.vendor = ''
  form.paid_at = new Date().toISOString().slice(0, 10)
  form.contract_id = ''
  form.customer_id = ''
  form.remark = ''
  dialogVisible.value = true
}

function openEdit(row: ExpenseListItem) {
  editingId.value = row.id
  form.expense_type = row.expense_type
  form.amount = row.amount
  form.vendor = row.vendor || ''
  form.paid_at = row.paid_at
  form.contract_id = row.contract_id || ''
  form.customer_id = row.customer_id || ''
  form.remark = row.remark || ''
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.expense_type || !form.amount || !form.paid_at) {
    ElMessage.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    const payload = {
      expense_type: form.expense_type,
      amount: form.amount,
      vendor: form.vendor || null,
      paid_at: form.paid_at,
      contract_id: form.contract_id || null,
      customer_id: form.customer_id || null,
      remark: form.remark || null,
    }
    if (editingId.value) {
      await expenseApi.update(editingId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await expenseApi.create(payload)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadList()
    loadStats()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: ExpenseListItem) {
  await ElMessageBox.confirm(`确认删除该条支出记录？`, '删除确认', { type: 'warning' })
  await expenseApi.remove(row.id)
  ElMessage.success('已删除')
  loadList()
  loadStats()
}

function fmt(val: number) {
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

onMounted(() => { loadList(); loadStats() })
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>支出管理</h2>
      <el-button type="primary" @click="openCreate">+ 新增支出</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px" v-if="stats">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">总支出</div>
          <div class="stat-value expense">¥ {{ fmt(stats.total_expense) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">总回款</div>
          <div class="stat-value revenue">¥ {{ fmt(stats.total_revenue) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">利润</div>
          <div class="stat-value" :class="stats.profit >= 0 ? 'profit-pos' : 'profit-neg'">
            ¥ {{ fmt(stats.profit) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">利润率</div>
          <div class="stat-value" :class="stats.profit_rate >= 0 ? 'profit-pos' : 'profit-neg'">
            {{ stats.profit_rate }}%
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 按类型明细 -->
    <el-card shadow="never" style="margin-bottom: 16px" v-if="stats && Object.keys(stats.by_type).length">
      <div style="display:flex; gap: 24px; flex-wrap: wrap">
        <div v-for="(val, key) in stats.by_type" :key="key" class="type-stat">
          <span class="type-label">{{ key }}</span>
          <span class="type-value">¥ {{ fmt(val) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 筛选 -->
    <el-card shadow="never" style="margin-bottom: 12px">
      <el-form inline>
        <el-form-item label="支出类型">
          <el-select v-model="query.expense_type" clearable placeholder="全部" style="width:120px">
            <el-option v-for="t in EXPENSE_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="付款日期">
          <el-date-picker v-model="query.date_from" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width:130px" />
          <span style="margin: 0 4px">~</span>
          <el-date-picker v-model="query.date_to" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width:130px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="付款日期" prop="paid_at" width="110" />
        <el-table-column label="类型" prop="expense_type" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTagType(row.expense_type)">{{ row.expense_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额(元)" prop="amount" width="120" align="right">
          <template #default="{ row }">
            <span style="font-weight:600">¥ {{ fmt(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="供应商/付给" prop="vendor" min-width="120" />
        <el-table-column label="关联合同" prop="contract_no" width="140" />
        <el-table-column label="关联客户" prop="customer_name" min-width="140" />
        <el-table-column label="备注" prop="remark" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 12px; justify-content: flex-end"
        @current-change="loadList"
      />
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑支出' : '新增支出'" width="500px">
      <el-form label-width="90px">
        <el-form-item label="支出类型" required>
          <el-select v-model="form.expense_type" style="width:100%">
            <el-option v-for="t in EXPENSE_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额(元)" required>
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="付款日期" required>
          <el-date-picker v-model="form.paid_at" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="form.vendor" placeholder="付给谁" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts">
function typeTagType(t: string) {
  const map: Record<string, string> = {
    '认证费': 'primary',
    '差旅': 'warning',
    '代理费': 'success',
    '测试费': 'info',
    '其他': '',
  }
  return map[t] || ''
}
export default { name: 'ExpenseList' }
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.stat-card { text-align: center; }
.stat-label { font-size: 13px; color: #888; margin-bottom: 6px; }
.stat-value { font-size: 22px; font-weight: 700; }
.expense { color: #e6a23c; }
.revenue { color: #409eff; }
.profit-pos { color: #67c23a; }
.profit-neg { color: #f56c6c; }
.type-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.type-label { font-size: 12px; color: #888; }
.type-value { font-size: 15px; font-weight: 600; color: #303133; }
</style>
