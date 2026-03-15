<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'
import AttachmentPanel from '@/components/common/AttachmentPanel.vue'

interface PaymentItem {
  id: string
  quotation_id: string
  quote_no: string
  customer_name: string | null
  total_amount: number
  received_amount: number
  status: string
  received_date: string | null
  payment_method: string | null
  remark: string | null
}

interface PaymentRecord {
  id: string
  payment_id: string
  amount: number
  received_date: string
  payment_method: string
  remark: string | null
  created_at: string
}

const loading = ref(false)
const list = ref<PaymentItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

const statusOptions = ['待收款', '部分收款', '已收款']
const methodOptions = ['对公转账', '现金', '支票', '其他']

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await request.get<any, { data: PaymentItem[]; total: number }>('/quotation-payments', { params })
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.status = ''; query.keyword = ''; query.page = 1; loadList() }

// ── 收款明细弹窗 ──────────────────────────────────────────────
const dialogVisible = ref(false)
const recordsLoading = ref(false)
const addingRecord = ref(false)
const editingItem = ref<PaymentItem | null>(null)
const records = ref<PaymentRecord[]>([])
const expandedRecordId = ref<string | null>(null)
const recordForm = reactive({
  amount: 0,
  received_date: '',
  payment_method: '对公转账',
  remark: '',
})

async function openRecordsDialog(row: PaymentItem) {
  editingItem.value = row
  records.value = []
  expandedRecordId.value = null
  recordForm.amount = Math.max(0, row.total_amount - row.received_amount)
  recordForm.received_date = new Date().toISOString().slice(0, 10)
  recordForm.payment_method = '对公转账'
  recordForm.remark = ''
  dialogVisible.value = true
  await loadRecords()
}

async function loadRecords() {
  recordsLoading.value = true
  try {
    const res = await request.get<any, { data: PaymentRecord[] }>(
      `/quotation-payments/${editingItem.value!.id}/records`
    )
    records.value = res.data
  } finally {
    recordsLoading.value = false
  }
}

async function addRecord() {
  if (!recordForm.received_date) { ElMessage.warning('请选择收款日期'); return }
  if (!recordForm.amount || recordForm.amount <= 0) { ElMessage.warning('请填写收款金额'); return }
  addingRecord.value = true
  try {
    await request.post(`/quotation-payments/${editingItem.value!.id}/records`, {
      amount: recordForm.amount,
      received_date: recordForm.received_date,
      payment_method: recordForm.payment_method,
      remark: recordForm.remark || null,
    })
    ElMessage.success('收款已登记')
    await loadRecords()
    loadList()
  } finally {
    addingRecord.value = false
  }
}

async function deleteRecord(rec: PaymentRecord) {
  await ElMessageBox.confirm('确认删除该收款记录？', '删除确认', { type: 'warning' })
  await request.delete(`/quotation-payments/${editingItem.value!.id}/records/${rec.id}`)
  ElMessage.success('已删除')
  await loadRecords()
  loadList()
}

async function handleDelete(row: PaymentItem) {
  await ElMessageBox.confirm('确认删除该收款记录？', '删除确认', { type: 'warning' })
  await request.delete(`/quotation-payments/${row.id}`)
  ElMessage.success('已删除')
  loadList()
}

function statusTagType(s: string) {
  if (s === '已收款') return 'success'
  if (s === '部分收款') return 'warning'
  return 'info'
}

function fmt(v: number) {
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

onMounted(() => loadList())
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>收款管理</h2>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" style="margin-bottom:12px">
      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width:110px">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户/报价单号">
          <el-input v-model="query.keyword" clearable placeholder="搜索" style="width:180px" />
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
        <el-table-column label="报价单号" prop="quote_no" width="150" />
        <el-table-column label="客户" prop="customer_name" min-width="160" />
        <el-table-column label="合同金额" width="130" align="right">
          <template #default="{ row }">¥ {{ fmt(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="已收金额" width="130" align="right">
          <template #default="{ row }">
            <span :style="row.received_amount > 0 ? 'color:#67c23a;font-weight:600' : ''">
              ¥ {{ fmt(row.received_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="待收金额" width="130" align="right">
          <template #default="{ row }">
            <span :style="row.total_amount - row.received_amount > 0 ? 'color:#e6a23c;font-weight:600' : ''">
              ¥ {{ fmt(row.total_amount - row.received_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRecordsDialog(row)">收款明细</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:12px;justify-content:flex-end"
        @current-change="loadList"
      />
    </el-card>

    <!-- 收款明细弹窗 -->
    <el-dialog v-model="dialogVisible" title="收款明细" width="700px" destroy-on-close>
      <!-- 头部汇总 -->
      <div v-if="editingItem" style="display:flex;gap:24px;margin-bottom:12px;font-size:13px;color:#606266;background:#f5f7fa;padding:10px 14px;border-radius:4px">
        <span>报价单：<b>{{ editingItem.quote_no }}</b></span>
        <span>客户：<b>{{ editingItem.customer_name }}</b></span>
        <span>合同金额：<b>¥ {{ fmt(editingItem.total_amount) }}</b></span>
        <span>已收：<b style="color:#67c23a">¥ {{ fmt(editingItem.received_amount) }}</b></span>
        <span>待收：<b style="color:#e6a23c">¥ {{ fmt(editingItem.total_amount - editingItem.received_amount) }}</b></span>
      </div>

      <!-- 历史收款记录 -->
      <div v-loading="recordsLoading" style="min-height:60px">
        <el-empty v-if="!recordsLoading && records.length === 0" description="暂无收款记录" :image-size="60" />
        <div v-for="rec in records" :key="rec.id" style="margin-bottom:8px;border:1px solid #ebeef5;border-radius:4px;padding:8px 12px">
          <el-row :gutter="8" align="middle">
            <el-col :span="4" style="font-size:13px">{{ rec.received_date }}</el-col>
            <el-col :span="4" style="font-weight:600;color:#67c23a;font-size:13px">¥ {{ fmt(rec.amount) }}</el-col>
            <el-col :span="4" style="font-size:13px">{{ rec.payment_method }}</el-col>
            <el-col :span="7" style="color:#909399;font-size:12px">{{ rec.remark || '-' }}</el-col>
            <el-col :span="3" style="text-align:right">
              <el-button link size="small" @click="expandedRecordId = expandedRecordId === rec.id ? null : rec.id">
                {{ expandedRecordId === rec.id ? '收起凭证' : '查看凭证' }}
              </el-button>
            </el-col>
            <el-col :span="2" style="text-align:right">
              <el-button link type="danger" size="small" @click="deleteRecord(rec)">删除</el-button>
            </el-col>
          </el-row>
          <div v-if="expandedRecordId === rec.id" style="margin-top:8px;border-top:1px dashed #ebeef5;padding-top:8px">
            <AttachmentPanel entity-type="payment_record" :entity-id="rec.id" />
          </div>
        </div>
      </div>

      <el-divider>登记新收款</el-divider>

      <!-- 新增收款表单 -->
      <el-form :inline="true" label-width="70px">
        <el-form-item label="金额" required>
          <el-input-number v-model="recordForm.amount" :min="0.01" :precision="2" style="width:130px" controls-position="right" />
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="recordForm.received_date" type="date" value-format="YYYY-MM-DD" style="width:140px" />
        </el-form-item>
        <el-form-item label="方式">
          <el-select v-model="recordForm.payment_method" style="width:110px">
            <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="recordForm.remark" style="width:130px" placeholder="可选" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="addingRecord" @click="addRecord">添加</el-button>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
</style>
