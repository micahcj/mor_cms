import type { TreeNode } from './static_resources2';

export function escapeHtml(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#039;');
}

// export function exportListHtml(tree: TreeNode): string {
// 	function render(nodes: TreeNode[]): string {
// 		return `<ul>${nodes
// 			.map((node) => {
// 				if (typeof node === 'string') {
// 					return `<li>${escapeHtml(node)}</li>`;
// 				}

// 				const [label, ...children] = node;

// 				return `<li>${escapeHtml(label)}${children.length ? render(children) : ''}</li>`;
// 			})
// 			.join('')}</ul>`;
// 	}

// 	return render(tree);
// }

export function exportListHtml(nodes: TreeNode[]): string {
	function render(list: TreeNode[]): string {
		return `<ul>${list
			.map(
				(node) =>
					`<li>${escapeHtml(node.text)}${node.children?.length ? render(node.children) : ''}</li>`
			)
			.join('')}</ul>`;
	}

	return render(nodes);
}

export function findNode(
	nodes: TreeNode[],
	id: string,
	parent: TreeNode | null = null
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
): { tree: TreeNode[] } | null {
	const copy = structuredClone(nodes);
	const from = findNode(copy, fromId);
	const to = findNode(copy, toId);
	if (!from || !to) return null;

	const fromContainer = from.parent ? from.parent.children! : copy;
	const [removed] = fromContainer.splice(from.index, 1);

	const toContainer = to.parent ? to.parent.children! : copy;
	const insertIndex = position === 'before' ? to.index : to.index + 1;
	toContainer.splice(insertIndex, 0, removed);

	return { tree: copy };
}

// export function moveNodeById(
// 	nodes: TreeNode[],
// 	fromId: string,
// 	toId: string,
// 	position: 'before' | 'after'
// ): TreeNode[] {
// 	if (fromId === toId) return nodes;

// 	const copy = structuredClone(nodes);
// 	const from = findNode(copy, fromId);
// 	const to = findNode(copy, toId);
// 	if (!from || !to) return nodes;

// 	const fromContainer = from.parent ? from.parent.children! : copy;
// 	const [removed] = fromContainer.splice(from.index, 1);

// 	const toContainer = to.parent ? to.parent.children! : copy;
// 	const insertIndex = position === 'before' ? to.index : to.index + 1;

// 	toContainer.splice(insertIndex, 0, removed);
// 	return copy;
// }

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

export function getDepth(nodes: TreeNode[], id: string): number {
	const found = findNode(nodes, id);

	if (!found) return 0;

	// parent chain = depth
	let depth = 0;
	let current = found.parent;

	while (current) {
		depth++;
		const parentFound = findNode(nodes, current.id);
		current = parentFound?.parent ?? null;
	}

	return depth;
}

export function canIndent(nodes: TreeNode[], id: string, maxDepth = 5): boolean {
	const found = findNode(nodes, id);
	if (!found) return false;
	if (found.index === 0) return false;
	return getDepth(found.path) < maxDepth;
}

export function canOutdent(nodes: TreeNode[], id: string): boolean {
	const found = findNode(nodes, id);
	return !!found?.parent;
}
