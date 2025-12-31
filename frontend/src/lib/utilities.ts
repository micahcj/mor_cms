type TreeNode = string | TreeGroup;
type TreeGroup = [string, ...TreeNode[]];
type ContentTree = TreeGroup[];

function escapeHtml(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#039;');
}

export function exportListHtml(tree: ContentTree): string {
	function render(nodes: TreeNode[]): string {
		return `<ul>${nodes
			.map((node) => {
				if (typeof node === 'string') {
					return `<li>${escapeHtml(node)}</li>`;
				}

				const [label, ...children] = node;

				return `<li>${escapeHtml(label)}${children.length ? render(children) : ''}</li>`;
			})
			.join('')}</ul>`;
	}

	return render(tree);
}
