/*
 * pp_printf.c -- a small printf, written from scratch for this package.
 *
 * Supported: %d %i %u %x %X %p %s %c %%, the '-' and '0' flags and a
 * field width.  Length modifiers (l, h, z) are accepted and ignored,
 * as everything is 32 bits here.  No floating point.
 *
 * The formatter emits one character at a time through a callback, so
 * printf needs no buffer and can't overflow one.
 */
#include <stdarg.h>
#include "types.h"
#include "io.h"

#define F_LEFT	1
#define F_ZERO	2

typedef void (*out_fn)(int c, void *arg);

static int emit_padded(out_fn out, void *arg, const char *s, int len,
		       int width, int flags, char sign)
{
	int n = 0, pad = width - len - (sign != 0);

	if (pad < 0)
		pad = 0;
	if (!(flags & F_LEFT) && !(flags & F_ZERO))
		for (; pad; pad--, n++)
			out(' ', arg);
	if (sign) {
		out(sign, arg);
		n++;
	}
	if (!(flags & F_LEFT))	/* zero padding goes after the sign */
		for (; pad; pad--, n++)
			out('0', arg);
	for (; len; len--, n++)
		out(*s++, arg);
	for (; pad; pad--, n++)	/* only left-justified is left here */
		out(' ', arg);
	return n;
}

static int pp_format(out_fn out, void *arg, const char *fmt, va_list ap)
{
	static const char digits[] = "0123456789abcdef0123456789ABCDEF";
	char tmp[12], *s, sign;
	int n = 0, flags, width, len, base, upper;
	u32 v;

	for (; *fmt; fmt++) {
		if (*fmt != '%') {
			out(*fmt, arg);
			n++;
			continue;
		}
		fmt++;
		flags = width = 0;
		for (;; fmt++) {
			if (*fmt == '-')
				flags |= F_LEFT;
			else if (*fmt == '0')
				flags |= F_ZERO;
			else
				break;
		}
		while (*fmt >= '0' && *fmt <= '9')
			width = width * 10 + *fmt++ - '0';
		while (*fmt == 'l' || *fmt == 'h' || *fmt == 'z')
			fmt++;

		sign = 0;
		base = 0;
		upper = 0;
		switch (*fmt) {
		case '\0':
			return n;
		case 'c':
			tmp[0] = va_arg(ap, int);
			n += emit_padded(out, arg, tmp, 1, width, flags & F_LEFT, 0);
			continue;
		case 's':
			s = va_arg(ap, char *);
			if (!s)
				s = "(null)";
			n += emit_padded(out, arg, s, strlen(s), width,
					 flags & F_LEFT, 0);
			continue;
		case 'd':
		case 'i':
			v = va_arg(ap, int);
			if ((s32)v < 0) {
				sign = '-';
				v = -v;
			}
			base = 10;
			break;
		case 'u':
			v = va_arg(ap, unsigned int);
			base = 10;
			break;
		case 'X':
			upper = 16;
			/* fall through */
		case 'x':
			v = va_arg(ap, unsigned int);
			base = 16;
			break;
		case 'p':
			v = (u32)va_arg(ap, void *);
			out('0', arg);
			out('x', arg);
			n += 2;
			base = 16;
			width = 8;
			flags = F_ZERO;
			break;
		default: /* '%' or unknown: print it verbatim */
			out(*fmt, arg);
			n++;
			continue;
		}

		/* Number: digits are built backwards at the end of tmp */
		s = tmp + sizeof(tmp);
		do {
			*--s = digits[upper + v % base];
			v /= base;
		} while (v);
		len = tmp + sizeof(tmp) - s;
		n += emit_padded(out, arg, s, len, width, flags, sign);
	}
	return n;
}

static void out_uart(int c, void *arg)
{
	putc(c);
}

static void out_buf(int c, void *arg)
{
	char **p = arg;

	*(*p)++ = c;
}

int pp_printf(const char *fmt, ...)
{
	va_list ap;
	int n;

	va_start(ap, fmt);
	n = pp_format(out_uart, 0, fmt, ap);
	va_end(ap);
	return n;
}

int pp_sprintf(char *buf, const char *fmt, ...)
{
	va_list ap;
	char *p = buf;
	int n;

	va_start(ap, fmt);
	n = pp_format(out_buf, &p, fmt, ap);
	va_end(ap);
	*p = '\0';
	return n;
}
