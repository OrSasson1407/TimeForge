/**
 * Translation dictionary (docs/02-PRD.md UX notes: English/Hebrew only).
 * A plain nested-key lookup rather than a library — the project avoids a
 * dependency for what a ~150-line module covers, matching the stdlib-only
 * choice already made for backend/app/core/security.py's HTTP calls.
 *
 * Covers the auth flow (Login/Register/Verify/ForgotPassword/
 * PendingApproval/CompleteProfile), the header, Availability, Constraints,
 * Audit, Security, and the Management/Schedule page trees (including the
 * generic EntityManager/DataTable/entityConfigs machinery they share).
 * AdminUsersPage and AdminPendingApprovalsPage still read English literals
 * directly; extending them is the same mechanical pattern (add keys here,
 * swap literals for t() calls).
 */

export type Language = 'en' | 'he'

export const LANGUAGES: { code: Language; label: string; dir: 'ltr' | 'rtl' }[] = [
  { code: 'en', label: 'English', dir: 'ltr' },
  { code: 'he', label: 'עברית', dir: 'rtl' },
]

const dictionary = {
  'app.name': { en: 'TimeForge', he: "טיים-פורג'" },
  'app.backendOnline': { en: 'Backend API: online', he: 'שרת הבק-אנד: מחובר' },
  'app.backendOffline': { en: 'Backend API: offline', he: 'שרת הבק-אנד: מנותק' },

  'nav.dashboard': { en: 'Dashboard', he: 'לוח בקרה' },
  'nav.schedule': { en: 'Schedule', he: 'מערכת שעות' },
  'nav.availability': { en: 'Availability', he: 'זמינות' },
  'nav.management': { en: 'Management', he: 'ניהול' },
  'nav.constraints': { en: 'Constraints', he: 'אילוצים' },
  'nav.audit': { en: 'Audit Log', he: 'יומן פעולות' },
  'nav.pendingApprovals': { en: 'Pending Approvals', he: 'ממתינים לאישור' },
  'nav.manageUsers': { en: 'Manage Users', he: 'ניהול משתמשים' },
  'nav.security': { en: 'Security', he: 'אבטחה' },
  'nav.signOut': { en: 'Sign out', he: 'התנתקות' },
  'nav.awaitingApproval': { en: 'awaiting approval', he: 'ממתין לאישור' },

  'login.title': { en: 'Welcome back', he: 'ברוכים השבים' },
  'login.subtitle': {
    en: 'Sign in to your TimeForge account.',
    he: 'התחברו לחשבון TimeForge שלכם.',
  },
  'login.verifiedNotice': {
    en: 'Email verified. Your account is awaiting administrator approval — you can sign in in the meantime.',
    he: 'האימייל אומת. החשבון שלכם ממתין לאישור מנהל — ניתן להתחבר בינתיים.',
  },
  'login.email': { en: 'Email', he: 'אימייל' },
  'login.password': { en: 'Password', he: 'סיסמה' },
  'login.forgotPassword': { en: 'Forgot password?', he: 'שכחתם סיסמה?' },
  'login.submit': { en: 'Sign in', he: 'התחברות' },
  'login.submitting': { en: 'Signing in…', he: 'מתחבר…' },
  'login.or': { en: 'or', he: 'או' },
  'login.google': { en: 'Continue with Google', he: 'המשך עם Google' },
  'login.googleConnecting': { en: 'Connecting…', he: 'מתחבר…' },
  'login.noAccount': { en: "Don't have an account?", he: 'אין לכם חשבון?' },
  'login.createOne': { en: 'Create one', he: 'צרו חשבון' },
  'login.invalidCredentials': { en: 'Invalid email or password.', he: 'אימייל או סיסמה שגויים.' },
  'login.googleFailed': {
    en: 'Google sign-in failed or was cancelled.',
    he: 'ההתחברות עם Google נכשלה או בוטלה.',
  },
  'login.noMatchingAccount': {
    en: 'Signed in with Firebase, but no matching TimeForge account was found.',
    he: 'ההתחברות ל-Firebase הצליחה, אך לא נמצא חשבון TimeForge תואם.',
  },

  'register.title': { en: 'Create your account', he: 'יצירת חשבון' },
  'register.subtitle': {
    en: 'Register, verify your email, and an administrator will approve your access.',
    he: 'הירשמו, אמתו את האימייל שלכם, ומנהל יאשר את הגישה שלכם.',
  },
  'register.fullName': { en: 'Full name', he: 'שם מלא' },
  'register.email': { en: 'Email', he: 'אימייל' },
  'register.school': { en: 'School', he: 'בית ספר' },
  'register.selectSchool': { en: 'Select your school', he: 'בחרו בית ספר' },
  'register.loadingSchools': { en: 'Loading schools…', he: 'טוען בתי ספר…' },
  'register.password': { en: 'Password', he: 'סיסמה' },
  'register.confirmPassword': { en: 'Confirm password', he: 'אימות סיסמה' },
  'register.recaptchaSkipped': {
    en: "reCAPTCHA isn't configured for this environment — skipping the challenge.",
    he: 'reCAPTCHA אינו מוגדר בסביבה זו — מדלגים על האתגר.',
  },
  'register.submit': { en: 'Create account', he: 'יצירת חשבון' },
  'register.submitting': { en: 'Creating account…', he: 'יוצר חשבון…' },
  'register.haveAccount': { en: 'Already have an account?', he: 'כבר יש לכם חשבון?' },
  'register.signIn': { en: 'Sign in', he: 'התחברות' },
  'register.errorWeakPassword': {
    en: 'Password does not meet the minimum strength requirements.',
    he: 'הסיסמה אינה עומדת בדרישות החוזק המינימליות.',
  },
  'register.errorPasswordMismatch': { en: 'Passwords do not match.', he: 'הסיסמאות אינן תואמות.' },
  'register.errorNoSchool': { en: 'Please select your school.', he: 'נא לבחור בית ספר.' },
  'register.errorNoRecaptcha': {
    en: 'Please complete the reCAPTCHA challenge.',
    he: 'נא להשלים את אתגר ה-reCAPTCHA.',
  },
  'register.errorGeneric': { en: 'Registration failed.', he: 'ההרשמה נכשלה.' },

  'verify.title': { en: 'Check your email', he: 'בדקו את תיבת הדואר' },
  'verify.subtitle': {
    en: 'We sent a 6-digit verification code to your email address. Enter it below to confirm your account.',
    he: 'שלחנו קוד אימות בן 6 ספרות לכתובת האימייל שלכם. הזינו אותו למטה כדי לאשר את החשבון.',
  },
  'verify.email': { en: 'Email', he: 'אימייל' },
  'verify.code': { en: 'Verification code', he: 'קוד אימות' },
  'verify.submit': { en: 'Verify email', he: 'אימות אימייל' },
  'verify.submitting': { en: 'Verifying…', he: 'מאמת…' },
  'verify.noCode': { en: "Didn't get a code?", he: 'לא קיבלתם קוד?' },
  'verify.resend': { en: 'Resend code', he: 'שליחה חוזרת' },
  'verify.resendIn': { en: 'Resend in {seconds}s', he: 'שליחה חוזרת בעוד {seconds} שניות' },
  'verify.resendSuccess': { en: 'A new code has been sent.', he: 'קוד חדש נשלח.' },
  'verify.backToSignIn': { en: 'Back to sign in', he: 'חזרה להתחברות' },
  'verify.errorGeneric': { en: 'Verification failed.', he: 'האימות נכשל.' },
  'verify.errorResend': { en: 'Could not resend the code.', he: 'לא ניתן היה לשלוח מחדש את הקוד.' },

  'forgot.title': { en: 'Reset your password', he: 'איפוס סיסמה' },
  'forgot.subtitle': {
    en: "Enter your account email and we'll send you a link to reset your password.",
    he: 'הזינו את כתובת האימייל של החשבון שלכם ונשלח לכם קישור לאיפוס הסיסמה.',
  },
  'forgot.sentNotice': {
    en: 'If an account exists for that email, a reset link is on its way. Check your inbox.',
    he: 'אם קיים חשבון עבור כתובת זו, קישור איפוס בדרך אליכם. בדקו את תיבת הדואר.',
  },
  'forgot.email': { en: 'Email', he: 'אימייל' },
  'forgot.submit': { en: 'Send reset link', he: 'שליחת קישור איפוס' },
  'forgot.submitting': { en: 'Sending…', he: 'שולח…' },
  'forgot.backToSignIn': { en: 'Back to sign in', he: 'חזרה להתחברות' },

  'pending.badge': { en: 'Pending approval', he: 'ממתין לאישור' },
  'pending.title': { en: 'Almost there, {name}', he: 'כמעט שם, {name}' },
  'pending.subtitle': {
    en: 'Your email is verified. An administrator at your school still needs to review and approve your account before you can sign in to TimeForge.',
    he: 'האימייל שלכם אומת. מנהל בבית הספר שלכם עדיין צריך לבדוק ולאשר את החשבון שלכם לפני שתוכלו להתחבר ל-TimeForge.',
  },
  'pending.hint': {
    en: "Check back later, or reach out to your school's administrator if this is taking longer than expected.",
    he: 'חזרו לבדוק מאוחר יותר, או פנו למנהל בית הספר שלכם אם זה לוקח יותר זמן מהצפוי.',
  },
  'pending.signOut': { en: 'Sign out', he: 'התנתקות' },

  'profile.title': { en: 'Just one more step', he: 'עוד צעד אחד' },
  'profile.subtitle': {
    en: '{email} is verified. Tell us your school to finish setting up your TimeForge account.',
    he: '{email} אומת. ספרו לנו מה בית הספר שלכם כדי לסיים את הקמת חשבון TimeForge שלכם.',
  },
  'profile.yourGoogleAccount': { en: 'Your Google account', he: 'חשבון ה-Google שלכם' },
  'profile.fullName': { en: 'Full name', he: 'שם מלא' },
  'profile.school': { en: 'School', he: 'בית ספר' },
  'profile.selectSchool': { en: 'Select your school', he: 'בחרו בית ספר' },
  'profile.loadingSchools': { en: 'Loading schools…', he: 'טוען בתי ספר…' },
  'profile.submit': { en: 'Continue', he: 'המשך' },
  'profile.submitting': { en: 'Finishing up…', he: 'מסיים…' },
  'profile.errorNoSchool': { en: 'Please select your school.', he: 'נא לבחור בית ספר.' },
  'profile.errorGeneric': {
    en: 'Could not complete your profile.',
    he: 'לא ניתן היה להשלים את הפרופיל שלכם.',
  },

  'common.loading': { en: 'Loading…', he: 'טוען…' },
  'common.retry': { en: 'Retry', he: 'ניסיון חוזר' },
  'common.dismiss': { en: 'Dismiss notification', he: 'סגירת התראה' },
  'common.offline': {
    en: "You're offline. Changes won't save until your connection comes back.",
    he: 'אתם לא מחוברים לרשת. שינויים לא יישמרו עד לחזרת החיבור.',
  },
  'common.backOnline': { en: "You're back online.", he: 'חזרתם להיות מחוברים.' },
  'common.close': { en: 'Close', he: 'סגירה' },
  'common.skipToContent': { en: 'Skip to main content', he: 'דלגו לתוכן הראשי' },

  'availability.title': { en: 'Availability', he: 'זמינות' },
  'availability.noTeacherRecord': {
    en: 'Your account has no linked teacher record, so there is no availability to submit.',
    he: 'לחשבון שלכם אין רשומת מורה מקושרת, ולכן אין זמינות להגיש.',
  },
  'availability.ownerType': { en: 'Owner type', he: 'סוג הבעלים' },
  'availability.teacher': { en: 'Teacher', he: 'מורה' },
  'availability.class': { en: 'Class', he: 'כיתה' },
  'availability.select': { en: 'Select…', he: 'בחרו…' },
  'availability.loading': { en: 'Loading…', he: 'טוען…' },
  'availability.selectOwner': {
    en: 'Select an owner to view their availability.',
    he: 'בחרו בעלים כדי לצפות בזמינות שלו.',
  },
  'availability.period': { en: 'Period', he: 'שיעור' },
  'availability.available': { en: 'Available', he: 'זמין' },
  'availability.unavailable': { en: 'Unavailable', he: 'לא זמין' },
  'constraints.title': { en: 'Constraint Configuration', he: 'הגדרות אילוצים' },
  'constraints.softWeights': { en: 'Soft-constraint weights', he: 'משקלי אילוצים רכים' },
  'constraints.solverParams': { en: 'Solver parameters', he: 'פרמטרי הפותר' },
  'constraints.timeoutSeconds': { en: 'Timeout (seconds)', he: 'זמן קצוב (שניות)' },
  'constraints.randomSeed': { en: 'Random seed', he: 'זרע אקראי' },
  'constraints.qualityDecay': { en: 'Quality decay (k)', he: 'דעיכת איכות (k)' },
  'constraints.saving': { en: 'Saving…', he: 'שומר…' },
  'constraints.save': { en: 'Save', he: 'שמירה' },
  'constraints.saved': { en: 'Saved.', he: 'נשמר.' },
  'security.title': { en: 'Security', he: 'אבטחה' },
  'security.subtitle': {
    en: 'Manage your password and active sessions.',
    he: 'ניהול הסיסמה וההתחברויות הפעילות שלכם.',
  },
  'security.changePassword': { en: 'Change password', he: 'שינוי סיסמה' },
  'security.changingPassword': { en: 'Changing password…', he: 'משנה סיסמה…' },
  'security.currentPassword': { en: 'Current password', he: 'סיסמה נוכחית' },
  'security.newPassword': { en: 'New password', he: 'סיסמה חדשה' },
  'security.confirmNewPassword': { en: 'Confirm new password', he: 'אימות סיסמה חדשה' },
  'security.passwordChanged': { en: 'Password changed.', he: 'הסיסמה שונתה.' },
  'security.errorWeakPassword': {
    en: 'Password does not meet the minimum strength requirements.',
    he: 'הסיסמה אינה עומדת בדרישות החוזק המינימליות.',
  },
  'security.errorPasswordMismatch': { en: 'Passwords do not match.', he: 'הסיסמאות אינן תואמות.' },
  'security.errorCurrentPasswordWrong': {
    en: 'Current password is incorrect.',
    he: 'הסיסמה הנוכחית שגויה.',
  },
  'security.googleAccountNotice': {
    en: 'You sign in with Google — manage your password from your Google account.',
    he: 'אתם מתחברים עם Google — נהלו את הסיסמה שלכם דרך חשבון ה-Google שלכם.',
  },
  'security.sessions': { en: 'Sessions', he: 'התחברויות' },
  'security.sessionsDescription': {
    en: 'Sign out of every device where you are currently signed in, including this one.',
    he: 'התנתקו מכל המכשירים שבהם אתם מחוברים כרגע, כולל מכשיר זה.',
  },
  'security.signedInAs': { en: 'Signed in as', he: 'מחוברים בתור' },
  'security.revokeSessions': { en: 'Sign out everywhere', he: 'התנתקות מכל מקום' },
  'security.revoking': { en: 'Signing out…', he: 'מתנתק…' },
  'security.revokeConfirmTitle': { en: 'Sign out everywhere?', he: 'להתנתק מכל מקום?' },
  'security.revokeConfirmMessage': {
    en: 'This immediately signs you out of every device, including this one — you will need to sign in again.',
    he: 'פעולה זו תנתק אתכם מיד מכל המכשירים, כולל מכשיר זה — תצטרכו להתחבר מחדש.',
  },
  'security.sessionsRevoked': { en: 'Signed out of all sessions.', he: 'התנתקתם מכל ההתחברויות.' },
  'security.errorRevokeFailed': {
    en: 'Could not sign out of other sessions. Try again.',
    he: 'לא ניתן היה להתנתק מהתחברויות אחרות. נסו שוב.',
  },
  'shortcuts.title': { en: 'Keyboard shortcuts', he: 'קיצורי מקלדת' },
  'shortcuts.hint': {
    en: 'Press ? anytime to show this list.',
    he: 'לחצו ? בכל עת כדי להציג רשימה זו.',
  },
  'shortcuts.home': { en: 'Go to Dashboard', he: 'מעבר ללוח הבקרה' },
  'shortcuts.schedule': { en: 'Go to Schedule', he: 'מעבר למערכת השעות' },
  'shortcuts.availability': { en: 'Go to Availability', he: 'מעבר לזמינות' },
  'shortcuts.management': { en: 'Go to Management (admin)', he: 'מעבר לניהול (מנהל)' },
  'shortcuts.users': { en: 'Go to Manage Users (admin)', he: 'מעבר לניהול משתמשים (מנהל)' },
  'shortcuts.help': { en: 'Show this help', he: 'הצגת עזרה זו' },
  'shortcuts.palette': { en: 'Open command palette', he: 'פתיחת סרגל פקודות' },

  'audit.title': { en: 'Audit Log', he: 'יומן פעולות' },
  'audit.entityType': { en: 'Entity type', he: 'סוג ישות' },
  'audit.entityId': { en: 'Entity ID', he: 'מזהה ישות' },
  'audit.search': { en: 'Search', he: 'חיפוש' },
  'audit.timestamp': { en: 'Timestamp', he: 'זמן' },
  'audit.operation': { en: 'Operation', he: 'פעולה' },
  'audit.actor': { en: 'Actor', he: 'מבצע' },
  'audit.reason': { en: 'Reason', he: 'סיבה' },
  'audit.noResults': { en: 'No audit events found.', he: 'לא נמצאו אירועי יומן.' },
  'audit.errorLoading': {
    en: 'Could not load audit events.',
    he: 'לא ניתן היה לטעון את אירועי היומן.',
  },
  'audit.emptyTitle': { en: 'Nothing here yet', he: 'עדיין אין כאן כלום' },
  'audit.emptyMessage': {
    en: 'Search by entity type and ID to see its history.',
    he: 'חפשו לפי סוג ישות ומזהה כדי לראות את ההיסטוריה שלה.',
  },

  // --- Schedule page + scheduling feature components ---
  'schedule.title': { en: 'Schedule', he: 'מערכת שעות' },
  'schedule.publishedNotice': {
    en: 'Showing the currently published schedule.',
    he: 'מוצגת מערכת השעות המפורסמת הנוכחית.',
  },
  'schedule.noPublishedNotice': {
    en: 'No schedule has been published yet.',
    he: 'עדיין לא פורסמה מערכת שעות.',
  },
  'schedule.timetable': { en: 'Timetable', he: 'מערכת שעות' },
  'schedule.print': { en: 'Print', he: 'הדפסה' },
  'schedule.viewBy': { en: 'View by', he: 'תצוגה לפי' },
  'schedule.class': { en: 'Class', he: 'כיתה' },
  'schedule.teacher': { en: 'Teacher', he: 'מורה' },
  'schedule.room': { en: 'Room', he: 'חדר' },
  'schedule.select': { en: 'Select…', he: 'בחרו…' },
  'schedule.period': { en: 'Period', he: 'שיעור' },
  'schedule.selectWhatToView': { en: 'Select what to view.', he: 'בחרו מה להציג.' },
  'schedule.generateOrSelect': {
    en: 'Generate or select a version above.',
    he: 'צרו או בחרו גרסה למעלה.',
  },
  'schedule.nothingToShowYet': { en: 'Nothing to show yet.', he: 'עדיין אין מה להציג.' },

  'generate.title': { en: 'Generate a schedule', he: 'יצירת מערכת שעות' },
  'generate.reason': { en: 'Reason (optional)', he: 'סיבה (לא חובה)' },
  'generate.submit': { en: 'Generate', he: 'יצירה' },
  'generate.submitting': { en: 'Generating…', he: 'יוצר…' },
  'generate.status': { en: 'Status: {status}', he: 'סטטוס: {status}' },
  'generate.createdDraft': {
    en: 'Created draft version {id} with {count} assignments',
    he: 'נוצרה טיוטת גרסה {id} עם {count} שיבוצים',
  },
  'generate.qualitySuffix': { en: ' — quality {quality}/100', he: ' — איכות {quality}/100' },
  'generate.infeasibleDefault': {
    en: 'No valid schedule could be found.',
    he: 'לא ניתן היה למצוא מערכת שעות תקינה.',
  },
  'generate.bottleneckLine': {
    en: '{subject}{capability}: needs {required}, only {available} available (short by {shortage}).',
    he: '{subject}{capability}: נדרשים {required}, זמינים {available} בלבד (חסרים {shortage}).',
  },
  'generate.bottleneckCapability': { en: ' (needs {capability})', he: ' (נדרש {capability})' },
  'generate.endedWithStatus': {
    en: 'Generation ended with status {status}.',
    he: 'היצירה הסתיימה בסטטוס {status}.',
  },

  'versions.title': { en: 'Versions', he: 'גרסאות' },
  'versions.id': { en: 'ID', he: 'מזהה' },
  'versions.status': { en: 'Status', he: 'סטטוס' },
  'versions.created': { en: 'Created', he: 'נוצר' },
  'versions.quality': { en: 'Quality', he: 'איכות' },
  'versions.hardViolations': { en: 'Hard violations', he: 'הפרות קשות' },
  'versions.selected': { en: 'Selected', he: 'נבחרה' },
  'versions.view': { en: 'View', he: 'הצגה' },
  'versions.empty': {
    en: 'No versions yet — generate one above.',
    he: 'עדיין אין גרסאות — צרו אחת למעלה.',
  },
  'versions.publish': { en: 'Publish this version', he: 'פרסום גרסה זו' },
  'versions.publishing': { en: 'Publishing…', he: 'מפרסם…' },
  'versions.cannotPublish': {
    en: 'This version still has hard-constraint violations and cannot be published.',
    he: 'לגרסה זו עדיין יש הפרות אילוצים קשים ולא ניתן לפרסם אותה.',
  },

  'compare.title': { en: 'Compare versions', he: 'השוואת גרסאות' },
  'compare.from': { en: 'From', he: 'מ-' },
  'compare.to': { en: 'To', he: 'עד' },
  'compare.select': { en: 'Select…', he: 'בחרו…' },
  'compare.unchanged': {
    en: '{count} assignments unchanged.',
    he: '{count} שיבוצים ללא שינוי.',
  },
  'compare.added': { en: 'Added', he: 'נוספו' },
  'compare.removed': { en: 'Removed', he: 'הוסרו' },
  'compare.moved': { en: 'Moved', he: 'הועברו' },
  'compare.noDifferences': { en: 'No differences.', he: 'אין הבדלים.' },
  'compare.lessonLine': {
    en: 'Lesson {id}: {before} → {after}',
    he: 'שיעור {id}: {before} ← {after}',
  },
  'compare.unassigned': { en: 'unassigned', he: 'לא משובץ' },

  'disruption.title': { en: 'Report a disruption', he: 'דיווח על שיבוש' },
  'disruption.whatUnavailable': {
    en: 'What became unavailable',
    he: 'מה הפך ללא זמין',
  },
  'disruption.aTeacher': { en: 'A teacher', he: 'מורה' },
  'disruption.aRoom': { en: 'A room', he: 'חדר' },
  'disruption.teacher': { en: 'Teacher', he: 'מורה' },
  'disruption.room': { en: 'Room', he: 'חדר' },
  'disruption.select': { en: 'Select…', he: 'בחרו…' },
  'disruption.affectedSlots': { en: 'Affected slots', he: 'משבצות מושפעות' },
  'disruption.period': { en: 'Period', he: 'שיעור' },
  'disruption.reason': { en: 'Reason', he: 'סיבה' },
  'disruption.submit': { en: 'Report and repair', he: 'דיווח ותיקון' },
  'disruption.submitting': { en: 'Repairing…', he: 'מתקן…' },
  'disruption.result': { en: 'Result: {status}', he: 'תוצאה: {status}' },
  'disruption.repaired': {
    en: 'Repaired — {moved} moved, {rooms} room change(s), {teachers} teacher change(s).',
    he: 'תוקן — {moved} הועברו, {rooms} שינויי חדר, {teachers} שינויי מורה.',
  },
  'disruption.noRepairFound': {
    en: 'No repair could be found.',
    he: 'לא נמצא תיקון אפשרי.',
  },
  'disruption.bottleneckLine': {
    en: '{subject}: needs {required}, only {available} available.',
    he: '{subject}: נדרשים {required}, זמינים {available} בלבד.',
  },

  'disruptionHistory.title': { en: 'Disruption history', he: 'היסטוריית שיבושים' },
  'disruptionHistory.reported': { en: 'Reported', he: 'דווח' },
  'disruptionHistory.type': { en: 'Type', he: 'סוג' },
  'disruptionHistory.target': { en: 'Target', he: 'יעד' },
  'disruptionHistory.affectedSlots': { en: 'Affected slots', he: 'משבצות מושפעות' },
  'disruptionHistory.reason': { en: 'Reason', he: 'סיבה' },
  'disruptionHistory.empty': {
    en: 'No disruptions reported yet.',
    he: 'עדיין לא דווחו שיבושים.',
  },

  'move.title': { en: 'Move assignment', he: 'העברת שיבוץ' },
  'move.teacher': { en: 'Teacher', he: 'מורה' },
  'move.room': { en: 'Room', he: 'חדר' },
  'move.day': { en: 'Day', he: 'יום' },
  'move.period': { en: 'Period', he: 'שיעור' },
  'move.validate': { en: 'Validate', he: 'אימות' },
  'move.validating': { en: 'Validating…', he: 'מאמת…' },
  'move.apply': { en: 'Apply', he: 'החלה' },
  'move.applying': { en: 'Applying…', he: 'מחיל…' },
  'move.cancel': { en: 'Cancel', he: 'ביטול' },
  'move.applied': { en: 'Move applied.', he: 'ההעברה הוחלה.' },
  'move.undo': { en: 'Undo', he: 'ביטול פעולה' },
  'move.undone': { en: 'Move undone.', he: 'ההעברה בוטלה.' },
  'move.undoFailed': { en: 'Could not undo the move.', he: 'לא ניתן היה לבטל את ההעברה.' },
  'move.moved': { en: 'Moved.', he: 'הועבר.' },
  'move.invalidSlot': {
    en: 'That slot is not valid for this lesson.',
    he: 'משבצת זו אינה תקינה עבור שיעור זה.',
  },
  'move.moveFailed': { en: 'Could not move this lesson.', he: 'לא ניתן היה להעביר שיעור זה.' },
  'move.violationSuffix': {
    en: ' — constraint violation: {details}',
    he: ' — הפרת אילוץ: {details}',
  },

  // --- Management page + shared admin-table components ---
  'management.title': { en: 'School Management', he: 'ניהול בית הספר' },
  'management.sectionsAriaLabel': { en: 'Management sections', he: 'אזורי ניהול' },

  'dataTable.search': { en: 'Search…', he: 'חיפוש…' },
  'dataTable.noRecords': { en: 'No records yet.', he: 'עדיין אין רשומות.' },
  'dataTable.noMatches': { en: 'No matches for "{query}".', he: 'אין תוצאות עבור "{query}".' },
  'dataTable.edit': { en: 'Edit', he: 'עריכה' },
  'dataTable.previous': { en: 'Previous', he: 'הקודם' },
  'dataTable.next': { en: 'Next', he: 'הבא' },
  'dataTable.pageOf': {
    en: 'Page {page} of {total} · {count} total',
    he: 'עמוד {page} מתוך {total} · סה"כ {count}',
  },

  'entityManager.new': { en: 'New', he: 'חדש' },
  'entityManager.editingHeading': { en: 'Edit: {id}', he: 'עריכה: {id}' },
  'entityManager.id': { en: 'ID', he: 'מזהה' },
  'entityManager.save': { en: 'Save', he: 'שמירה' },
  'entityManager.saving': { en: 'Saving…', he: 'שומר…' },
  'entityManager.cancel': { en: 'Cancel', he: 'ביטול' },
  'entityManager.editAriaLabel': { en: 'Edit {title}', he: 'עריכת {title}' },
  'entityManager.newAriaLabel': { en: 'New {title}', he: '{title} חדש' },

  'catalog.teachers.title': { en: 'Teachers', he: 'מורים' },
  'catalog.teachers.name': { en: 'Name', he: 'שם' },
  'catalog.teachers.email': { en: 'Email', he: 'דוא"ל' },
  'catalog.teachers.subjectIds': {
    en: 'Subjects (comma-separated subject IDs)',
    he: 'מקצועות (מזהי מקצוע מופרדים בפסיקים)',
  },
  'catalog.teachers.subjectIdsHelp': { en: 'e.g. MATH, SCI', he: 'לדוגמה: MATH, SCI' },
  'catalog.teachers.maxWeeklyLoad': { en: 'Max weekly load', he: 'עומס שבועי מרבי' },
  'catalog.teachers.maxConsecutive': {
    en: 'Max consecutive lessons',
    he: 'מספר שיעורים רצופים מרבי',
  },
  'catalog.teachers.columnSubjects': { en: 'Subjects', he: 'מקצועות' },

  'catalog.classes.title': { en: 'Classes', he: 'כיתות' },
  'catalog.classes.name': { en: 'Name', he: 'שם' },
  'catalog.classes.grade': { en: 'Grade', he: 'שכבה' },
  'catalog.classes.studentCount': { en: 'Student count', he: 'מספר תלמידים' },
  'catalog.classes.homeRoomId': { en: 'Home room ID (optional)', he: 'מזהה חדר בית (לא חובה)' },
  'catalog.classes.columnStudents': { en: 'Students', he: 'תלמידים' },

  'catalog.subjects.title': { en: 'Subjects', he: 'מקצועות' },
  'catalog.subjects.name': { en: 'Name', he: 'שם' },
  'catalog.subjects.code': { en: 'Code', he: 'קוד' },
  'catalog.subjects.requiredCapability': {
    en: 'Required room capability (optional)',
    he: 'יכולת חדר נדרשת (לא חובה)',
  },
  'catalog.subjects.maxDailyOccurrences': {
    en: 'Max daily occurrences',
    he: 'מספר מופעים יומי מרבי',
  },
  'catalog.subjects.minSpacingDays': { en: 'Min spacing (days)', he: 'מרווח מינימלי (ימים)' },
  'catalog.subjects.columnCapability': { en: 'Required capability', he: 'יכולת נדרשת' },

  'catalog.rooms.title': { en: 'Rooms', he: 'חדרים' },
  'catalog.rooms.name': { en: 'Name', he: 'שם' },
  'catalog.rooms.capacity': { en: 'Capacity', he: 'קיבולת' },
  'catalog.rooms.roomType': { en: 'Room type', he: 'סוג חדר' },
  'catalog.rooms.roomTypeHelp': { en: 'e.g. STANDARD, LAB', he: 'לדוגמה: STANDARD, LAB' },
  'catalog.rooms.capabilities': {
    en: 'Capabilities (comma-separated)',
    he: 'יכולות (מופרדות בפסיקים)',
  },
  'catalog.rooms.status': { en: 'Status', he: 'סטטוס' },

  'catalog.schoolDays.title': { en: 'School Days', he: 'ימי לימוד' },
  'catalog.schoolDays.weekday': { en: 'Weekday', he: 'יום בשבוע' },
  'catalog.schoolDays.isActive': { en: 'Active', he: 'פעיל' },

  'catalog.timePeriods.title': { en: 'Time Periods', he: 'שיעורי זמן' },
  'catalog.timePeriods.index': { en: 'Order index', he: 'מיקום בסדר' },
  'catalog.timePeriods.startTime': { en: 'Start time (HH:MM:SS)', he: 'שעת התחלה (HH:MM:SS)' },
  'catalog.timePeriods.endTime': { en: 'End time (HH:MM:SS)', he: 'שעת סיום (HH:MM:SS)' },
  'catalog.timePeriods.kind': { en: 'Kind', he: 'סוג' },
  'catalog.timePeriods.columnOrder': { en: 'Order', he: 'סדר' },
  'catalog.timePeriods.columnTime': { en: 'Time', he: 'זמן' },

  'catalog.lessonRequirements.title': { en: 'Lesson Requirements', he: 'דרישות שיעור' },
  'catalog.lessonRequirements.classId': { en: 'Class ID', he: 'מזהה כיתה' },
  'catalog.lessonRequirements.subjectId': { en: 'Subject ID', he: 'מזהה מקצוע' },
  'catalog.lessonRequirements.weeklyPeriods': { en: 'Weekly periods', he: 'שיעורים שבועיים' },
  'catalog.lessonRequirements.requiredCapability': {
    en: 'Required room capability (optional)',
    he: 'יכולת חדר נדרשת (לא חובה)',
  },
  'catalog.lessonRequirements.columnClass': { en: 'Class', he: 'כיתה' },
  'catalog.lessonRequirements.columnSubject': { en: 'Subject', he: 'מקצוע' },

  'csvImport.button': { en: 'Import from CSV', he: 'ייבוא מ-CSV' },
  'csvImport.title': { en: 'Import teachers from CSV', he: 'ייבוא מורים מקובץ CSV' },
  'csvImport.help': {
    en: "Columns: id, name, email, subject_ids (semicolon-separated), max_weekly_load, max_consecutive. An existing id overwrites that teacher's record.",
    he: 'עמודות: id, name, email, subject_ids (מופרדות בנקודה-פסיק), max_weekly_load, max_consecutive. מזהה קיים ידרוס את רשומת המורה הזו.',
  },
  'csvImport.fileLabel': { en: 'CSV file', he: 'קובץ CSV' },
  'csvImport.columnId': { en: 'ID', he: 'מזהה' },
  'csvImport.columnName': { en: 'Name', he: 'שם' },
  'csvImport.columnEmail': { en: 'Email', he: 'דוא"ל' },
  'csvImport.columnStatus': { en: 'Status', he: 'סטטוס' },
  'csvImport.ok': { en: 'OK', he: 'תקין' },
  'csvImport.rowsReady': {
    en: '{count} row(s) ready to import',
    he: '{count} שורות מוכנות לייבוא',
  },
  'csvImport.rowsWithErrors': {
    en: ', {count} row(s) with errors (skipped)',
    he: ', {count} שורות עם שגיאות (דולגו)',
  },
  'csvImport.importButton': { en: 'Import {count} teacher(s)', he: 'ייבוא {count} מורים' },
  'csvImport.importing': { en: 'Importing…', he: 'מייבא…' },
  'csvImport.cancel': { en: 'Cancel', he: 'ביטול' },
  'csvImport.resultSuccess': { en: 'Imported {count} teacher(s).', he: 'יובאו {count} מורים.' },
  'csvImport.resultPartial': {
    en: 'Imported {count} teacher(s), {failed} failed.',
    he: 'יובאו {count} מורים, {failed} נכשלו.',
  },
  'csvImport.missingId': { en: 'missing id', he: 'חסר מזהה' },
  'csvImport.missingName': { en: 'missing name', he: 'חסר שם' },
  'csvImport.missingEmail': { en: 'missing email', he: 'חסר דוא"ל' },
  'csvImport.invalidMaxWeeklyLoad': {
    en: 'invalid max_weekly_load',
    he: 'max_weekly_load לא תקין',
  },
  'csvImport.invalidMaxConsecutive': {
    en: 'invalid max_consecutive',
    he: 'max_consecutive לא תקין',
  },
} as const

export type TranslationKey = keyof typeof dictionary

export function translate(
  key: TranslationKey,
  language: Language,
  vars?: Record<string, string | number>,
): string {
  let text: string = dictionary[key][language] ?? dictionary[key].en
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      text = text.replace(`{${name}}`, String(value))
    }
  }
  return text
}
