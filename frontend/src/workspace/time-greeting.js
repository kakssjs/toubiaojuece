const WEEKDAYS = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']

export function greetingForHour(hour) {
  if (hour < 5 || hour >= 23) return '夜深了'
  if (hour < 11) return '上午好'
  if (hour < 13) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

export function formatWorkspaceDate(date) {
  return `${date.getFullYear()} 年 ${date.getMonth() + 1} 月 ${date.getDate()} 日 · ${WEEKDAYS[date.getDay()]}`
}
