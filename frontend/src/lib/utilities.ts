import type { TreeNode } from './static_resources';

function escapeHtml(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#039;');
}

export function exportListHtml(tree: TreeNode): string {
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

export function findNode(
	nodes: TreeNode[],
	id: string,
	parent: TreeNode | null
): { node: TreeNode; parent: TreeNode | null; index: number } | null {
	for (let i = 0; i < nodes.length; i++) {
		const node = nodes[i];
		if (node.id === id) return { node, parent, index: i };

		if (node.children) {
			const found = findNode(node.children, id, node);
			if (found) return found;
		}
	}
	return null;
}

export function moveNodeById(
	nodes: TreeNode[],
	fromId: string,
	toId: string,
	position: 'before' | 'after'
): TreeNode[] {
	if (fromId === toId) return nodes;

	const copy = structuredClone(nodes);
	const from = findNode(copy, fromId);
	const to = findNode(copy, toId);
	if (!from || !to) return nodes;

	const fromContainer = from.parent ? from.parent.children! : copy;
	const [removed] = fromContainer.splice(from.index, 1);

	const toContainer = to.parent ? to.parent.children! : copy;
	const insertIndex = position === 'before' ? to.index : to.index + 1;

	toContainer.splice(insertIndex, 0, removed);
	return copy;
}

export function indentNode(nodes: TreeNode[], id: string): TreeNode[] {
	const copy = structuredClone(nodes);
	const found = findNode(copy, id);
	if (!found) return nodes;

	const container = found.parent ? found.parent.children! : copy;
	if (found.index === 0) return nodes;

	const newParent = container[found.index - 1];
	newParent.children ??= [];

	const [removed] = container.splice(found.index, 1);
	newParent.children.push(removed);

	return copy;
}

export function outdentNode(nodes: TreeNode[], id: string): TreeNode[] {
	const copy = structuredClone(nodes);
	const found = findNode(copy, id);
	if (!found || !found.parent) return nodes;

	const parent = found.parent;
	const grand = findNode(copy, parent.id);
	if (!grand) return nodes;

	const parentContainer = grand.parent ? grand.parent.children! : copy;

	parent.children!.splice(found.index, 1);
	parentContainer.splice(grand.index + 1, 0, found.node);

	return copy;
}
