
import unicodedata

def normalize_text(s: str):
	"""
	- Remove accents but preserve ñ
	- Lowercase and strip
	"""
	if not s:
		return ""

	normalized = unicodedata.normalize("NFD", s)
	# Keep combining tilde (U+0303) so 'n' + '\u0303' can be recomposed back to 'ñ'
	cleaned = "".join(
		c for c in normalized
		if (unicodedata.category(c) != "Mn" or c == '\u0303')
	)
	# Recompose so preserved combining tilde becomes a precomposed 'ñ'
	return unicodedata.normalize("NFC", cleaned).lower().strip()
